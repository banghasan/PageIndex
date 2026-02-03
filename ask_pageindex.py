import argparse
import json
import os
import re

from pageindex.utils import ChatGPT_API, ConfigLoader


def iter_nodes(node):
    if isinstance(node, list):
        for item in node:
            yield from iter_nodes(item)
        return
    yield node
    for child in node.get("nodes", []) or []:
        yield from iter_nodes(child)


def normalize_text(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip().lower()


def score_node(node, query_terms):
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


def node_context(node, use_summary):
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


def build_prompt(question, contexts):
    joined = "\n\n---\n\n".join(contexts)
    return (
        "Gunakan konteks berikut untuk menjawab pertanyaan pengguna secara singkat dan jelas.\n"
        "Jika jawabannya tidak ditemukan, katakan bahwa informasinya tidak ada di konteks.\n\n"
        f"KONTEKS:\n{joined}\n\n"
        f"PERTANYAAN: {question}\n\n"
        "JAWABAN:"
    )


def main():
    parser = argparse.ArgumentParser(description="Tanya jawab dari hasil PageIndex")
    parser.add_argument(
        "--index_path", type=str, required=True, help="Path ke file *_structure.json"
    )
    parser.add_argument(
        "--question", type=str, required=True, help="Pertanyaan pengguna"
    )
    parser.add_argument(
        "--top_k", type=int, default=None, help="Jumlah node teratas (override env)"
    )
    parser.add_argument(
        "--model", type=str, default=None, help="Model override (opsional)"
    )
    args = parser.parse_args()

    if not os.path.isfile(args.index_path):
        raise ValueError(f"Index tidak ditemukan: {args.index_path}")

    with open(args.index_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    structure = data.get("structure")
    if not structure:
        raise ValueError("File index tidak memiliki field 'structure'")

    env_top_k = os.getenv("PAGEINDEX_QA_TOP_K")
    top_k = args.top_k or (int(env_top_k) if env_top_k else 3)
    use_summary = (os.getenv("PAGEINDEX_QA_USE_SUMMARY") or "yes").lower()

    query_terms = [t for t in normalize_text(args.question).split(" ") if t]

    nodes = list(iter_nodes(structure))
    scored = sorted(
        ((score_node(n, query_terms), n) for n in nodes),
        key=lambda x: x[0],
        reverse=True,
    )

    top_nodes = [n for score, n in scored if score > 0][:top_k]
    if not top_nodes:
        top_nodes = nodes[:top_k]

    contexts = [node_context(n, use_summary) for n in top_nodes]

    config_loader = ConfigLoader()
    user_opt = {}
    if args.model:
        user_opt["model"] = args.model
    opt = config_loader.load(user_opt)

    prompt = build_prompt(args.question, contexts)
    answer = ChatGPT_API(model=opt.model, prompt=prompt)
    print(answer)


if __name__ == "__main__":
    main()
