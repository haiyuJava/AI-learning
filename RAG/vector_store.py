import faiss
import numpy as np

class VectorStore:

    def __init__(self, dimension):
        # 使用内积计算相似度
        self.index = faiss.IndexFlatIP(dimension)
        self.id_map = []  # 保存 Chunk 对应 id 或 metadata

    def add(self, vectors, chunk_ids):
        """
        vectors: list of numpy arrays
        chunk_ids: list of chunk id 或 metadata
        """
        vectors = np.array(vectors).astype('float32')
        self.index.add(vectors)
        self.id_map.extend(chunk_ids)

    def search(self, query_vector, top_k=5):
        """
        query_vector: numpy array shape (dim,)
        """
        query_vector = np.array([query_vector]).astype('float32')
        scores, indices = self.index.search(query_vector, top_k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            results.append({
                "score": float(score),
                "chunk_id": self.id_map[idx]
            })
        return results