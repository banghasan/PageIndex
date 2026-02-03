# PageIndex API (Dokumentasi Singkat)

## Menjalankan server
```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

## Endpoint

### 1) Buat index dari PDF/Markdown
**POST** `/index`

Contoh (PDF):
```bash
curl -X POST "http://localhost:8000/index" \
  -H "Content-Type: application/json" \
  -d '{
    "pdf_path": "/home/banghasan/Calibre Library/user/Ahmad Sarwat, Lc (223)/Ahmad Sarwat, Lc - user.pdf"
  }'
```

Contoh (Markdown):
```bash
curl -X POST "http://localhost:8000/index" \
  -H "Content-Type: application/json" \
  -d '{
    "md_path": "/path/to/document.md"
  }'
```

Respons:
```json
{
  "book_id": "Ahmad Sarwat, Lc - user",
  "index_path": "/home/DATA/py/PageIndex/results/Ahmad Sarwat, Lc - user_structure.json"
}
```

### 2) Tanya‑jawab dari satu atau banyak buku
**POST** `/ask`

Tanya semua buku yang sudah di‑index:
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Bagian mana yang paling menarik?"
  }'
```

Tanya buku tertentu (berdasarkan `book_id`):
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Apa inti pembahasan bab 2?",
    "books": ["Ahmad Sarwat, Lc - user"]
  }'
```

Tanya dengan path index langsung:
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Apa kesimpulan utamanya?",
    "index_paths": ["/home/DATA/py/PageIndex/results/Ahmad Sarwat, Lc - user_structure.json"]
  }'
```

### 3) List buku yang sudah di‑index
**GET** `/books`

```bash
curl "http://localhost:8000/books"
```

Contoh respons:
```json
{
  "books": [
    {
      "book_id": "Ahmad Sarwat, Lc - user",
      "index_path": "/home/DATA/py/PageIndex/results/Ahmad Sarwat, Lc - user_structure.json"
    }
  ]
}
```

## Catatan konfigurasi
Atur default Q&A via `.env`:
```
PAGEINDEX_QA_TOP_K=3
PAGEINDEX_QA_USE_SUMMARY=yes
```
