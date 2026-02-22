import chromadb
from chromadb.config import Settings
from typing import Optional, List
from app.config import get_settings

settings = get_settings()


# Pre-defined regulatory documents for RAG
REGULATORY_DOCUMENTS = {
    "fincen_structuring": {
        "title": "FinCEN Guidance on Structuring",
        "content": """Structuring refers to the practice of conducting financial transactions in a specific
pattern calculated to avoid triggering reporting requirements. Under 31 U.S.C. § 5324, it is illegal
to structure transactions to evade Bank Secrecy Act reporting requirements. Key indicators include:
- Multiple deposits or withdrawals just below the $10,000 CTR threshold
- Breaking up large transactions into smaller ones across multiple days
- Using multiple branches or accounts to avoid detection
- Transactions by the same individual at multiple locations on the same day
Financial institutions must file SARs when structuring is suspected, even if the underlying
funds are legitimate.""",
        "typology": "structuring",
        "code": "31a",
    },
    "fincen_layering": {
        "title": "FinCEN Guidance on Money Laundering - Layering",
        "content": """Layering is the second stage of money laundering, where the criminal attempts to
distance the funds from their illegal source through complex financial transactions. This stage
is characterized by:
- Multiple transfers between accounts or jurisdictions
- Conversion between different forms of value
- Use of shell companies or nominees
- Circular transactions that return funds to the original source
- Wire transfers to and from offshore jurisdictions
The goal is to create a complex audit trail that makes it difficult for investigators to
trace the origins of the funds.""",
        "typology": "layering",
        "code": "31z",
    },
    "fatf_recommendation_20": {
        "title": "FATF Recommendation 20 - Reporting of Suspicious Transactions",
        "content": """If a financial institution suspects or has reasonable grounds to suspect that
funds are the proceeds of a criminal activity, or are related to terrorist financing, it should
be required, by law, to report promptly its suspicions to the financial intelligence unit (FIU).

Key requirements:
- Report suspicious transactions regardless of the amount
- Report attempted transactions that are abandoned
- Protected reporting - staff should be protected from liability
- Tipping off prohibition - do not inform the customer of the report
- Maintain records of all reports for at least 5 years""",
        "typology": "general",
        "code": "general",
    },
    "fincen_collection_account": {
        "title": "FinCEN Guidance on Collection Account Activity",
        "content": """Collection account patterns involve accounts that receive funds from multiple
unrelated sources, often followed by rapid consolidation and movement of funds. Indicators include:
- Numerous incoming transfers from unrelated parties
- Funds quickly consolidated and moved to another location
- Account holder unable to explain the source of funds
- No apparent business purpose for the activity
- Deposits followed by immediate withdrawals or transfers
This pattern is often associated with funnel accounts used in fraud schemes or money laundering.""",
        "typology": "collection_account",
        "code": "31z",
    },
    "fincen_rapid_movement": {
        "title": "FinCEN Guidance on Rapid Movement of Funds",
        "content": """Rapid movement of funds refers to the immediate or near-immediate transfer of
incoming funds out of an account. This is suspicious because legitimate account holders typically
allow funds to settle or use them for ongoing expenses. Key indicators:
- Funds transferred within hours of receipt
- No accumulation or use of funds in the account
- Transfers to high-risk jurisdictions
- Use of wire transfers for immediate movement
- No apparent business relationship between sender and receiver""",
        "typology": "rapid_movement",
        "code": "31z",
    },
    "india_pmla": {
        "title": "Prevention of Money Laundering Act, 2002 (India)",
        "content": """The Prevention of Money Laundering Act (PMLA) requires reporting entities in India
to maintain records of transactions and report suspicious transactions to the Financial Intelligence
Unit - India (FIU-IND). Key thresholds:
- Cash transactions exceeding ₹10 lakh (₹1,000,000)
- Series of cash transactions totaling ₹10 lakh in a month
- All suspicious transactions regardless of amount
- Cross-border wire transfers exceeding ₹5 lakh

Reporting entities must verify customer identity through KYC procedures and maintain transaction
records for 5 years after the transaction is completed.""",
        "typology": "general",
        "code": "general",
    },
}


class VectorStore:
    """
    Vector store for RAG using ChromaDB.
    Stores regulatory documents, typologies, and historical SARs.
    """

    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_directory,
            settings=Settings(anonymized_telemetry=False),
        )
        self._init_collections()
        self._initialized_regulatory = False

    def _init_collections(self):
        """Initialize collections for different document types."""
        # Collection for FinCEN typologies
        self.typologies = self.client.get_or_create_collection(
            name="fincen_typologies",
            metadata={"description": "FinCEN SAR typology definitions"},
        )

        # Collection for FATF guidelines
        self.fatf = self.client.get_or_create_collection(
            name="fatf_guidelines",
            metadata={"description": "FATF 40 Recommendations"},
        )

        # Collection for historical SARs
        self.historical_sars = self.client.get_or_create_collection(
            name="historical_sars",
            metadata={"description": "Approved SAR examples"},
        )

        # Collection for regulatory documents (RAG)
        self.regulatory_docs = self.client.get_or_create_collection(
            name="regulatory_documents",
            metadata={"description": "Regulatory guidance documents for RAG"},
        )

    def initialize_regulatory_documents(self, embedding_service):
        """
        Initialize the vector store with regulatory documents.
        Should be called once at startup.
        """
        if self._initialized_regulatory:
            return

        # Check if documents already exist
        if self.regulatory_docs.count() >= len(REGULATORY_DOCUMENTS):
            self._initialized_regulatory = True
            return

        print("Initializing regulatory documents in vector store...")

        for doc_id, doc in REGULATORY_DOCUMENTS.items():
            # Generate embedding
            embedding = embedding_service.embed(doc["content"])

            # Add to collection
            try:
                self.regulatory_docs.add(
                    ids=[doc_id],
                    embeddings=[embedding],
                    documents=[doc["content"]],
                    metadatas=[{
                        "title": doc["title"],
                        "typology": doc["typology"],
                        "code": doc["code"],
                        "type": "regulatory",
                    }],
                )
            except Exception as e:
                # Document might already exist
                print(f"Note: {doc_id} may already exist: {e}")

        self._initialized_regulatory = True
        print(f"Initialized {len(REGULATORY_DOCUMENTS)} regulatory documents")

    def add_typology(
        self,
        code: str,
        name: str,
        description: str,
        indicators: list[str],
        embedding: list[float],
    ):
        """Add a FinCEN typology to the vector store."""
        doc_id = f"typology_{code}"
        content = f"{name}: {description}. Indicators: {', '.join(indicators)}"

        self.typologies.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[{
                "code": code,
                "name": name,
                "type": "typology",
            }],
        )

    def add_historical_sar(
        self,
        sar_id: str,
        narrative: str,
        typology: str,
        embedding: list[float],
    ):
        """Add an approved SAR to the historical collection."""
        self.historical_sars.add(
            ids=[sar_id],
            embeddings=[embedding],
            documents=[narrative],
            metadatas=[{
                "typology": typology,
                "type": "historical_sar",
            }],
        )

    def search_typologies(
        self,
        query_embedding: list[float],
        n_results: int = 3,
    ) -> list[dict]:
        """Search for relevant typologies."""
        results = self.typologies.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
        )

        return self._format_results(results)

    def search_similar_sars(
        self,
        query_embedding: list[float],
        n_results: int = 3,
        typology_filter: Optional[str] = None,
    ) -> list[dict]:
        """Search for similar historical SARs."""
        where_filter = {"typology": typology_filter} if typology_filter else None

        results = self.historical_sars.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter,
        )

        return self._format_results(results)

    def search_regulatory_context(
        self,
        query_embedding: list[float],
        n_results: int = 3,
        typology_filter: Optional[str] = None,
    ) -> list[dict]:
        """
        Search for relevant regulatory context for RAG.

        Args:
            query_embedding: Embedding of the query text
            n_results: Number of results to return
            typology_filter: Optional filter by typology

        Returns:
            List of relevant regulatory documents
        """
        where_filter = {"typology": typology_filter} if typology_filter else None

        results = self.regulatory_docs.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter,
        )

        return self._format_results(results)

    def get_regulatory_context_for_typology(self, typology: str) -> List[dict]:
        """
        Get regulatory context directly by typology name (no embedding needed).

        Args:
            typology: The typology name (e.g., "structuring", "layering")

        Returns:
            List of relevant regulatory documents
        """
        # Normalize typology name
        typology_key = typology.lower().replace(" ", "_").replace("-", "_")

        # Handle common variations
        typology_mappings = {
            "money_laundering_layering": "layering",
            "money_laundering": "layering",
            "rapid_fund_movement": "rapid_movement",
        }
        typology_key = typology_mappings.get(typology_key, typology_key)

        # Get matching documents
        results = []

        # First, get specific typology documents
        for doc_id, doc in REGULATORY_DOCUMENTS.items():
            if doc["typology"] == typology_key or doc["typology"] == "general":
                results.append({
                    "document": doc["content"],
                    "metadata": {
                        "title": doc["title"],
                        "typology": doc["typology"],
                        "code": doc["code"],
                    },
                    "similarity": 1.0 if doc["typology"] == typology_key else 0.8,
                })

        # Sort by relevance (specific typology first)
        results.sort(key=lambda x: x["similarity"], reverse=True)

        return results[:3]

    def get_rag_context(
        self,
        facts: dict,
        typology: str,
        embedding_service=None,
    ) -> dict:
        """
        Get comprehensive RAG context for narrative generation.

        Args:
            facts: Transaction facts dictionary
            typology: Classified typology
            embedding_service: Optional embedding service for semantic search

        Returns:
            Dictionary with regulatory context, similar SARs, etc.
        """
        context = {
            "regulatory_guidance": [],
            "similar_sars": [],
            "typology_info": {},
        }

        # Get regulatory context by typology
        regulatory_docs = self.get_regulatory_context_for_typology(typology)
        context["regulatory_guidance"] = [
            {
                "title": doc["metadata"]["title"],
                "content": doc["document"][:500] + "..." if len(doc["document"]) > 500 else doc["document"],
                "relevance": doc["similarity"],
            }
            for doc in regulatory_docs
        ]

        # If embedding service is available, do semantic search
        if embedding_service:
            # Create query from facts
            query_text = self._build_query_from_facts(facts, typology)
            query_embedding = embedding_service.embed(query_text)

            # Search for similar historical SARs
            similar_sars = self.search_similar_sars(
                query_embedding=query_embedding,
                n_results=2,
                typology_filter=typology.lower().replace(" ", "_"),
            )
            context["similar_sars"] = similar_sars

        return context

    def _build_query_from_facts(self, facts: dict, typology: str) -> str:
        """Build a query string from facts for semantic search."""
        parts = [typology]

        if facts.get("scenario"):
            parts.append(facts["scenario"])

        patterns = facts.get("patterns", [])
        if patterns:
            parts.extend(patterns[:3])

        return ". ".join(parts)

    def _format_results(self, results: dict) -> list[dict]:
        """Format ChromaDB results into a cleaner structure."""
        formatted = []

        if not results or not results.get("documents"):
            return formatted

        documents = results["documents"][0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for i, doc in enumerate(documents):
            formatted.append({
                "document": doc,
                "metadata": metadatas[i] if i < len(metadatas) else {},
                "similarity": 1 - distances[i] if i < len(distances) else 0,
            })

        return formatted

    def get_collection_stats(self) -> dict:
        """Get statistics about the collections."""
        return {
            "typologies_count": self.typologies.count(),
            "fatf_count": self.fatf.count(),
            "historical_sars_count": self.historical_sars.count(),
            "regulatory_docs_count": self.regulatory_docs.count(),
        }


# Singleton instance
_vector_store_instance: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Get or create the vector store singleton."""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore()
    return _vector_store_instance
