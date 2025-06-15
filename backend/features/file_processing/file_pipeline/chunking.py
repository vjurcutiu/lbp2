def chunk_text(text: str, chunk_size: int = 1500, overlap: int = 400) -> list[str]:
    """
    Splits `text` into chunks of up to `chunk_size` characters with `overlap` characters between chunks.
    Returns a list of text chunks.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and less than chunk_size")

    chunks = []
    start = 0
    text_length = len(text)
    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks
