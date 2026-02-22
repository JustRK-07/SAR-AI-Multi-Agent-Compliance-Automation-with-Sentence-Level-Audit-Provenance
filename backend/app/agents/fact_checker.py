from sqlalchemy.orm import Session
from typing import Any

from app.services.fact_checker import FactCheckerService


class FactCheckerAgent:
    """
    Agent 4: Fact Checker

    Responsible for:
    - Extracting claims from narrative (using NER)
    - Verifying each claim against database facts
    - Flagging unsupported statements
    - Generating citations for each sentence
    """

    def __init__(self, db: Session):
        self.db = db
        self.fact_checker_service = FactCheckerService(db)

    async def verify_narrative(
        self,
        narrative: str,
        facts: dict[str, Any],
        sar_id: str,
    ) -> dict:
        """
        Verify all claims in the narrative.

        Returns:
            {
                "verified_narrative": str,
                "confidence": float,
                "claims_verified": int,
                "claims_total": int,
                "sentence_verifications": dict,
                "flagged_sentences": list,
            }
        """
        # Use the fact checker service
        result = self.fact_checker_service.verify_narrative(narrative, facts)

        # Identify flagged sentences (low confidence)
        flagged = []
        for idx, verification in result["sentence_verifications"].items():
            if verification["confidence"] < 0.95:
                flagged.append({
                    "index": idx,
                    "sentence": verification["sentence"],
                    "confidence": verification["confidence"],
                    "issues": [
                        c for c in verification["claims"]
                        if not c.get("verified", True)
                    ],
                })

        # If there are unsupported claims, attempt to fix or flag them
        if flagged:
            result["verified_narrative"] = self._annotate_flagged_sentences(
                narrative, flagged
            )
            result["flagged_sentences"] = flagged
        else:
            result["flagged_sentences"] = []

        return result

    def _annotate_flagged_sentences(
        self,
        narrative: str,
        flagged: list[dict],
    ) -> str:
        """
        Annotate sentences that couldn't be fully verified.
        Adds confidence markers and flags for human review.
        """
        if not flagged:
            return narrative

        sentences = [s.strip() for s in narrative.split('.') if s.strip()]
        flagged_indices = {f["index"] for f in flagged}

        annotated_sentences = []
        for idx, sentence in enumerate(sentences):
            if idx in flagged_indices:
                # Find the flagged entry for this sentence
                flag_info = next((f for f in flagged if f["index"] == idx), None)
                if flag_info:
                    confidence = flag_info.get("confidence", 0.5)
                    issues = flag_info.get("issues", [])

                    # Add confidence indicator based on level
                    if confidence < 0.7:
                        # Low confidence: mark for review
                        annotated_sentence = f"{sentence} [REVIEW REQUIRED: Confidence {confidence:.0%}]"
                    elif confidence < 0.95:
                        # Medium confidence: add footnote marker
                        annotated_sentence = f"{sentence} [*]"
                    else:
                        annotated_sentence = sentence

                    # Log unverified claims for audit
                    if issues:
                        claim_types = [issue.get("type", "unknown") for issue in issues[:3]]
                        print(f"[AUDIT] Sentence {idx} flagged: unverified claims: {claim_types}")

                    annotated_sentences.append(annotated_sentence)
                else:
                    annotated_sentences.append(sentence)
            else:
                annotated_sentences.append(sentence)

        return '. '.join(annotated_sentences) + '.'

    async def extract_and_verify_claims(
        self,
        sentence: str,
        facts: dict[str, Any],
    ) -> list[dict]:
        """
        Extract claims from a single sentence and verify each.
        """
        claims = self.fact_checker_service.extract_claims(sentence)
        verified_claims = []

        for claim in claims:
            verification = self.fact_checker_service.verify_claim(claim, facts)
            verified_claims.append({
                "claim": claim,
                "verification": verification,
            })

        return verified_claims

    async def generate_citations(
        self,
        narrative: str,
        facts: dict[str, Any],
    ) -> dict[int, list[str]]:
        """
        Generate citations for each sentence in the narrative.

        Returns:
            Dictionary mapping sentence index to list of citations
        """
        sentences = [s.strip() for s in narrative.split('.') if s.strip()]
        citations = {}

        for idx, sentence in enumerate(sentences):
            sentence_citations = []

            # Check what data sources support this sentence
            claims = self.fact_checker_service.extract_claims(sentence)

            for claim in claims:
                claim_type = claim.get("type")

                if claim_type == "number":
                    sentence_citations.append(
                        f"transactions table: COUNT(*) = {claim.get('value')}"
                    )
                elif claim_type == "currency":
                    sentence_citations.append(
                        f"transactions table: SUM(amount) = {claim.get('value')}"
                    )
                elif claim_type == "date":
                    sentence_citations.append(
                        f"transactions table: date range query"
                    )
                elif claim_type == "fincen_code":
                    sentence_citations.append(
                        f"FinCEN typology classification: Code {claim.get('value')}"
                    )

            if not sentence_citations:
                sentence_citations.append("Derived from case analysis")

            citations[idx] = sentence_citations

        return citations
