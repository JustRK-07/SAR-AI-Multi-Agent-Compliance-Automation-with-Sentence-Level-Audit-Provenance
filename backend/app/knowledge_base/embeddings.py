from sentence_transformers import SentenceTransformer
from typing import Union
from app.config import get_settings

settings = get_settings()


class EmbeddingService:
    """
    Service for generating text embeddings using sentence-transformers.
    """

    def __init__(self):
        self.model = SentenceTransformer(settings.embedding_model)

    def embed(self, text: Union[str, list[str]]) -> list[float]:
        """
        Generate embedding for text.

        Args:
            text: Single string or list of strings

        Returns:
            Embedding vector(s)
        """
        if isinstance(text, str):
            embedding = self.model.encode(text)
            return embedding.tolist()
        else:
            embeddings = self.model.encode(text)
            return [e.tolist() for e in embeddings]

    def embed_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """
        Generate embeddings for a batch of texts.

        Args:
            texts: List of strings to embed
            batch_size: Batch size for encoding

        Returns:
            List of embedding vectors
        """
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
        )
        return [e.tolist() for e in embeddings]

    def similarity(self, text1: str, text2: str) -> float:
        """
        Calculate cosine similarity between two texts.
        """
        from sentence_transformers.util import cos_sim

        emb1 = self.model.encode(text1)
        emb2 = self.model.encode(text2)

        similarity = cos_sim(emb1, emb2)
        return float(similarity[0][0])
