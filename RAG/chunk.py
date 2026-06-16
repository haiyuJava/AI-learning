def chunk_text(
        text,
        chunk_size=1000,
        overlap=200
):
    chunks = []

    start = 0
    chunk_id = 0

    while start < len(text):

        end = start + chunk_size

        chunk = {
            "id": chunk_id,
            "text": text[start:end]
        }

        chunks.append(chunk)

        chunk_id += 1

        start += chunk_size - overlap

    return chunks