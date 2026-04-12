"""Download sentence-transformers model to cache"""
from sentence_transformers import SentenceTransformer

print("Downloading sentence-transformers model...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("✓ Model downloaded and cached!")
print(f"  Dimensions: {model.get_sentence_embedding_dimension()}")
