import numpy as np
from sentence_transformers import SentenceTransformer

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.utils import create_documents
import faiss

# สร้างโฟลเดอร์ถ้าไม่มี
os.makedirs("embeddings", exist_ok=True)
os.makedirs("index", exist_ok=True)

# โหลดเอกสาร
documents = create_documents()

# โหลด model
model = SentenceTransformer('all-MiniLM-L6-v2')

# สร้าง embedding
embeddings = np.array([model.encode(doc['content']) for doc in documents]).astype('float32')

# เก็บ embedding
np.save("embeddings/embeddings.npy", embeddings)

# สร้าง FAISS index
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

# เก็บ index
faiss.write_index(index, "index/faiss_index.index")

# เก็บ mapping id -> document
import pickle
with open("index/id_map.pkl", "wb") as f:
    pickle.dump({i: doc for i, doc in enumerate(documents)}, f)