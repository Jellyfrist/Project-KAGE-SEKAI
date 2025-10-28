import os, glob, json, re
from uuid import uuid4

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CORPUS_FILE = os.path.join(BASE_DIR, "corpus.jsonl")


def clean_text(t):
    t = t.replace("\r\n", "\n")
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", "[EMAIL]", t)
    t = re.sub(r"\b0\d{8,9}\b", "[PHONE]", t)
    return t

def chunk_text(text, chunk_size=300, overlap=50):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks

def load_all_json(data_dir=DATA_DIR):
    docs = []
    for path in glob.glob(os.path.join(data_dir, "*.json")):
        fn = os.path.basename(path)
        with open(path, "r", encoding="utf-8") as f:
            arr = json.load(f)
        for item in arr:
            prod_id = item.get("product_id", None)
            if "question" in item and "solution" in item:
                text = f"Q: {item['question']}\nA: {item['solution']}"
                src_type = "faq"
            elif "complaint" in item:
                text = f"Complaint: {item.get('complaint')}\nDetail: {item.get('detail','')}"
                src_type = "complaint"
            else:
                text = json.dumps(item, ensure_ascii=False)
                src_type = "product"
            docs.append({
                "id": str(uuid4()),
                "product_id": prod_id,
                "source_file": fn,
                "source_type": src_type,
                "content": clean_text(text),
                "raw": item
            })
    return docs

def main():
    docs = load_all_json()
    chunks = []
    for d in docs:
        for c in chunk_text(d["content"]):
            chunks.append({
                "chunk_id": str(uuid4()),
                "product_id": d["product_id"],
                "source_file": d["source_file"],
                "source_type": d["source_type"],
                "text": c
            })
    # save corpus
    with open(CORPUS_FILE, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"[INFO] Saved {len(chunks)} chunks to {CORPUS_FILE}")

if __name__ == "__main__":
    main()
