```
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install --upgrade -r requirements.txt
```
Lalu
```
python3 run_pageindex.py --pdf_path /path/to/your/document.pdf
```

pakai pilihan model:

```
python3 run_pageindex.py --pdf_path "/path/to/file.pdf" --model gpt-5.2
```
