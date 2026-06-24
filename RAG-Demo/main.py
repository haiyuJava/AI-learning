from documents import load_pdf
from chunk import chunk_text
from embedding import EmbeddingModel
from prompt import build_prompt
from vector_store import VectorStore

from openai import OpenAI


client = OpenAI(
    api_key="your_deepseek_api_key",
    base_url="https://api.deepseek.com",
)


def ask_question(query, chunks, embedding_model, store, top_k=5):
    query_vector = embedding_model.encode([query])[0]

    results = store.search(query_vector, top_k=top_k)
    context_chunks = [chunks[r["chunk_id"]]["text"] for r in results]

    prompt_text = build_prompt(query, context_chunks)

    response = client.chat.completions.create(
        model="qwen-v1",
        messages=[{"role": "user", "content": prompt_text}],
        temperature=0.0,
    )

    return response.choices[0].message.content


def main():
    text = load_pdf("../data/Fluent in Python.pdf")

    chunks = chunk_text(text, chunk_size=1000, overlap=200)

    embedding_model = EmbeddingModel()
    vectors = embedding_model.encode([chunk["text"] for chunk in chunks])

    store = VectorStore(dimension=len(vectors[0]))
    store.add(vectors, [chunk["id"] for chunk in chunks])

    query = "Python list comprehension usage"
    query_vector = embedding_model.encode([query])[0]

    results = store.search(query_vector, top_k=3)

    print("Search results Top 3:")
    for r in results:
        chunk_id = r["chunk_id"]
        print(f"Chunk ID: {chunk_id}, Score: {r['score']}")
        print(chunks[chunk_id]["text"][:300])
        print("-" * 50)


if __name__ == "__main__":
    main()
