import os, json
from dotenv import load_dotenv
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.docstore.document import Document

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

CORPUS_FILE = "corpus.jsonl"
PERSIST_DIR = "chroma_db"

def main():
    emb = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=OPENAI_API_KEY)
    
    # load corpus
    docs = []
    with open(CORPUS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            doc = Document(
                page_content=item["text"],
                metadata={
                    "chunk_id": item["chunk_id"],
                    "product_id": item["product_id"],
                    "source_file": item["source_file"],
                    "source_type": item["source_type"]
                }
            )
            docs.append(doc)
    
    # create Chroma vector store
    db = Chroma.from_documents(
        docs,
        embedding=emb,
        persist_directory=PERSIST_DIR,
        collection_name="kage_products"
    )
    db.persist()
    print(f"[INFO] Indexed {len(docs)} chunks in {PERSIST_DIR}")

if __name__ == "__main__":
    main()
