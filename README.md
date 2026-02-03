# PageIndex (Versi Modifikasi)

Repositori ini adalah versi modifikasi dari PageIndex untuk membuat struktur (index) dokumen panjang (PDF/Markdown) dan memungkinkan tanya‑jawab berbasis hasil index.

Referensi sumber GitHub asli:
- https://github.com/VectifyAI/PageIndex

## Ringkasan Fitur
- Membuat struktur dokumen (tree index) dari PDF atau Markdown.
- Tanya‑jawab dari hasil index lewat CLI.
- API sederhana untuk membuat index, tanya‑jawab multi‑buku, dan daftar buku yang sudah di‑index.

## Instalasi
```bash
pip install -r requirements.txt
```

## Konfigurasi
Buat file `.env` di root proyek:
```
CHATGPT_API_KEY=your_openai_key_here
OPENAI_BASE_URL=http://localhost:8317/v1
PAGEINDEX_MODEL=gpt-5.2

# Default untuk Q&A
PAGEINDEX_QA_TOP_K=3
PAGEINDEX_QA_USE_SUMMARY=yes
```

## Cara Pakai (CLI)
### 1) Membuat index dari PDF
```bash
python3 run_pageindex.py --pdf_path /path/to/your/document.pdf
```

### 2) Membuat index dari Markdown
```bash
python3 run_pageindex.py --md_path /path/to/your/document.md
```

### 3) Tanya‑jawab dari index
```bash
python3 ask_pageindex.py --index_path results/your_document_structure.json --question "Pertanyaannya apa?"
```

## Cara Pakai (API)
Jalankan server:
```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

Dokumentasi API dan contoh `curl` ada di:
```
API.md
```

## Contoh Alur Pemakaian
1) Buat index dari PDF:
```bash
python3 run_pageindex.py --pdf_path /path/to/your/document.pdf
```

2) Tanya isi buku:
```bash
python3 ask_pageindex.py --index_path results/your_document_structure.json --question "Bagian mana yang paling menarik?"
```

3) (Opsional) Gunakan API untuk Q&A multi‑buku dan listing index.
