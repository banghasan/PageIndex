from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from pageindex import page_index_main
from pageindex.page_index_md import md_to_tree
from pageindex.utils import ChatGPT_API, ConfigLoader

APP_ROOT = Path(__file__).resolve().parent
RESULTS_DIR = APP_ROOT / "results"


def iter_nodes(node):
    if isinstance(node, list):
        for item in node:
            yield from iter_nodes(item)
        return
    yield node
    for child in node.get("nodes", []) or []:
        yield from iter_nodes(child)


def normalize_text(text: Optional[str]) -> str:
    if not text:
        return ""
    return " ".join(str(text).split()).strip().lower()


def score_node(node, query_terms: List[str]) -> int:
    hay = " ".join(
        [
            normalize_text(node.get("title")),
            normalize_text(node.get("summary")),
            normalize_text(node.get("text")),
        ]
    )
    if not hay:
        return 0
    return sum(1 for term in query_terms if term in hay)


def node_context(node, use_summary: str) -> str:
    title = node.get("title") or "(Tanpa judul)"
    summary = node.get("summary")
    text = node.get("text")

    if use_summary == "yes":
        body = summary or text or ""
    else:
        body = text or summary or ""

    page_info = (
        node.get("page_num") or node.get("page_range") or node.get("page_number") or ""
    )
    if page_info:
        return f"Judul: {title}\nHalaman: {page_info}\nIsi: {body}"
    return f"Judul: {title}\nIsi: {body}"


def build_prompt(question: str, contexts: List[str]) -> str:
    joined = "\n\n---\n\n".join(contexts)
    return (
        "Gunakan konteks berikut untuk menjawab pertanyaan pengguna secara singkat dan jelas.\n"
        "Jika jawabannya tidak ditemukan, katakan bahwa informasinya tidak ada di konteks.\n\n"
        f"KONTEKS:\n{joined}\n\n"
        f"PERTANYAAN: {question}\n\n"
        "JAWABAN:"
    )


def list_index_files() -> List[Path]:
    if not RESULTS_DIR.exists():
        return []
    return sorted(RESULTS_DIR.glob("*_structure.json"))


def book_id_from_path(path: Path) -> str:
    name = path.name
    if name.endswith("_structure.json"):
        return name[: -len("_structure.json")]
    return path.stem


class IndexRequest(BaseModel):
    pdf_path: Optional[str] = None
    md_path: Optional[str] = None
    model: Optional[str] = None
    toc_check_pages: Optional[int] = Field(default=None, ge=1)
    max_pages_per_node: Optional[int] = Field(default=None, ge=1)
    max_tokens_per_node: Optional[int] = Field(default=None, ge=1)
    if_add_node_id: Optional[str] = None
    if_add_node_summary: Optional[str] = None
    if_add_doc_description: Optional[str] = None
    if_add_node_text: Optional[str] = None
    if_thinning: Optional[str] = None
    thinning_threshold: Optional[int] = Field(default=None, ge=1)
    summary_token_threshold: Optional[int] = Field(default=None, ge=1)


class IndexResponse(BaseModel):
    book_id: str
    index_path: str


class AskRequest(BaseModel):
    question: str
    books: Optional[List[str]] = None
    index_paths: Optional[List[str]] = None
    top_k: Optional[int] = Field(default=None, ge=1)
    model: Optional[str] = None


class AskResponse(BaseModel):
    answer: str
    used_books: List[str]
    used_index_paths: List[str]


app = FastAPI(title="PageIndex API")


@app.post("/index", response_model=IndexResponse)
def create_index(payload: IndexRequest):
    if bool(payload.pdf_path) == bool(payload.md_path):
        raise HTTPException(
            status_code=400, detail="Pilih salah satu: pdf_path atau md_path"
        )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    if payload.pdf_path:
        pdf_path = payload.pdf_path
        if not pdf_path.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="PDF harus berekstensi .pdf")
        if not os.path.isfile(pdf_path):
            raise HTTPException(
                status_code=404, detail=f"PDF tidak ditemukan: {pdf_path}"
            )

        config_loader = ConfigLoader()
        user_opt = {}
        if payload.model:
            user_opt["model"] = payload.model
        if payload.toc_check_pages is not None:
            user_opt["toc_check_page_num"] = payload.toc_check_pages
        if payload.max_pages_per_node is not None:
            user_opt["max_page_num_each_node"] = payload.max_pages_per_node
        if payload.max_tokens_per_node is not None:
            user_opt["max_token_num_each_node"] = payload.max_tokens_per_node
        if payload.if_add_node_id is not None:
            user_opt["if_add_node_id"] = payload.if_add_node_id
        if payload.if_add_node_summary is not None:
            user_opt["if_add_node_summary"] = payload.if_add_node_summary
        if payload.if_add_doc_description is not None:
            user_opt["if_add_doc_description"] = payload.if_add_doc_description
        if payload.if_add_node_text is not None:
            user_opt["if_add_node_text"] = payload.if_add_node_text

        opt = config_loader.load(user_opt)
        toc_with_page_number = page_index_main(pdf_path, opt)

        book_id = Path(pdf_path).stem
        output_path = RESULTS_DIR / f"{book_id}_structure.json"
        output_path.write_text(
            json_dumps(toc_with_page_number),
            encoding="utf-8",
        )
        return IndexResponse(book_id=book_id, index_path=str(output_path))

    md_path = payload.md_path
    if not md_path.lower().endswith((".md", ".markdown")):
        raise HTTPException(
            status_code=400, detail="Markdown harus berekstensi .md/.markdown"
        )
    if not os.path.isfile(md_path):
        raise HTTPException(
            status_code=404, detail=f"Markdown tidak ditemukan: {md_path}"
        )

    config_loader = ConfigLoader()
    user_opt = {}
    if payload.model:
        user_opt["model"] = payload.model
    if payload.if_add_node_summary is not None:
        user_opt["if_add_node_summary"] = payload.if_add_node_summary
    if payload.if_add_doc_description is not None:
        user_opt["if_add_doc_description"] = payload.if_add_doc_description
    if payload.if_add_node_text is not None:
        user_opt["if_add_node_text"] = payload.if_add_node_text
    if payload.if_add_node_id is not None:
        user_opt["if_add_node_id"] = payload.if_add_node_id

    opt = config_loader.load(user_opt)
    toc_with_page_number = asyncio.run(
        md_to_tree(
            md_path=md_path,
            if_thinning=(payload.if_thinning or "no").lower() == "yes",
            min_token_threshold=payload.thinning_threshold or 5000,
            if_add_node_summary=opt.if_add_node_summary,
            summary_token_threshold=payload.summary_token_threshold or 200,
            model=opt.model,
            if_add_doc_description=opt.if_add_doc_description,
            if_add_node_text=opt.if_add_node_text,
            if_add_node_id=opt.if_add_node_id,
        )
    )

    book_id = Path(md_path).stem
    output_path = RESULTS_DIR / f"{book_id}_structure.json"
    output_path.write_text(
        json_dumps(toc_with_page_number),
        encoding="utf-8",
    )
    return IndexResponse(book_id=book_id, index_path=str(output_path))


@app.get("/books")
def list_books():
    files = list_index_files()
    return {
        "books": [
            {"book_id": book_id_from_path(p), "index_path": str(p)} for p in files
        ]
    }


@app.post("/ask", response_model=AskResponse)
def ask_question(payload: AskRequest):
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Pertanyaan tidak boleh kosong")

    index_paths: List[Path] = []
    if payload.index_paths:
        for p in payload.index_paths:
            path = Path(p)
            if not path.is_file():
                raise HTTPException(
                    status_code=404, detail=f"Index tidak ditemukan: {p}"
                )
            index_paths.append(path)
    elif payload.books:
        for book_id in payload.books:
            path = RESULTS_DIR / f"{book_id}_structure.json"
            if not path.is_file():
                raise HTTPException(
                    status_code=404, detail=f"Index tidak ditemukan: {path}"
                )
            index_paths.append(path)
    else:
        index_paths = list_index_files()

    if not index_paths:
        raise HTTPException(status_code=404, detail="Belum ada index")

    env_top_k = os.getenv("PAGEINDEX_QA_TOP_K")
    top_k = payload.top_k or (int(env_top_k) if env_top_k else 3)
    use_summary = (os.getenv("PAGEINDEX_QA_USE_SUMMARY") or "yes").lower()

    query_terms = [t for t in normalize_text(payload.question).split(" ") if t]

    selected_contexts: List[str] = []
    used_books: List[str] = []
    used_index_paths: List[str] = []

    for index_path in index_paths:
        data = json_load(index_path)
        structure = data.get("structure")
        if not structure:
            continue

        nodes = list(iter_nodes(structure))
        scored = sorted(
            ((score_node(n, query_terms), n) for n in nodes),
            key=lambda x: x[0],
            reverse=True,
        )
        top_nodes = [n for score, n in scored if score > 0][:top_k]
        if not top_nodes:
            top_nodes = nodes[:top_k]

        selected_contexts.extend([node_context(n, use_summary) for n in top_nodes])
        used_books.append(book_id_from_path(index_path))
        used_index_paths.append(str(index_path))

    if not selected_contexts:
        raise HTTPException(status_code=404, detail="Konteks tidak ditemukan")

    config_loader = ConfigLoader()
    user_opt = {}
    if payload.model:
        user_opt["model"] = payload.model
    opt = config_loader.load(user_opt)

    prompt = build_prompt(payload.question, selected_contexts)
    answer = ChatGPT_API(model=opt.model, prompt=prompt)
    return AskResponse(
        answer=answer,
        used_books=used_books,
        used_index_paths=used_index_paths,
    )


def json_load(path: Path):
    import json

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def json_dumps(data) -> str:
    import json

    return json.dumps(data, indent=2, ensure_ascii=False)
