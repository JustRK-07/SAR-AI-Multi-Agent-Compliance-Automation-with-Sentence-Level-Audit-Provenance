from sqlalchemy.orm import Session
from typing import Any
import re
from datetime import datetime
from dateutil import parser as date_parser


class FactCheckerService:
    """
    Service for verifying claims in SAR narratives against database facts.
    """

    def __init__(self, db: Session):
        self.db = db

    def extract_claims(self, narrative: str) -> list[dict]:
        """
        Extract factual claims from narrative text.
        Returns list of claims with their types and values.
        """
        claims = []

        # Pattern: Numbers (amounts, counts)
        number_pattern = r'(\d+(?:,\d{3})*(?:\.\d+)?)'
        numbers = re.findall(number_pattern, narrative)
        for num in numbers:
            clean_num = float(num.replace(',', ''))
            claims.append({
                "type": "number",
                "text": num,
                "value": clean_num,
            })

        # Pattern: Currency amounts (₹ or Rs.)
        currency_pattern = r'[₹Rs\.]+\s*(\d+(?:,\d{3})*(?:\.\d+)?(?:\s*(?:lakh|lakhs|L|crore|cr))?)'
        currencies = re.findall(currency_pattern, narrative, re.IGNORECASE)
        for curr in currencies:
            value = self._parse_indian_currency(curr)
            claims.append({
                "type": "currency",
                "text": curr,
                "value": value,
            })

        # Pattern: Date ranges
        date_pattern = r'(\w+\s+\d{1,2}(?:-\d{1,2})?,?\s*\d{4})'
        dates = re.findall(date_pattern, narrative)
        for date in dates:
            claims.append({
                "type": "date",
                "text": date,
                "value": date,
            })

        # Pattern: Account references
        account_pattern = r'(?:account|Account)\s*#?\s*(\*{0,4}\d{4,})'
        accounts = re.findall(account_pattern, narrative)
        for acc in accounts:
            claims.append({
                "type": "account",
                "text": acc,
                "value": acc,
            })

        # Pattern: FinCEN codes
        fincen_pattern = r'FinCEN\s*(?:Code|Activity)?\s*(\d{2}[a-z]?)'
        fincen_codes = re.findall(fincen_pattern, narrative, re.IGNORECASE)
        for code in fincen_codes:
            claims.append({
                "type": "fincen_code",
                "text": code,
                "value": code.lower(),
            })

        return claims

    def _parse_indian_currency(self, text: str) -> float:
        """Parse Indian currency format (lakhs, crores) to float."""
        text = text.lower().replace(',', '').strip()

        multiplier = 1
        if 'crore' in text or 'cr' in text:
            multiplier = 10000000
            text = re.sub(r'\s*(crore|cr)s?', '', text)
        elif 'lakh' in text or 'l' in text:
            multiplier = 100000
            text = re.sub(r'\s*(lakh|l)s?', '', text)

        try:
            base_value = float(re.sub(r'[^\d.]', '', text))
            return base_value * multiplier
        except ValueError:
            return 0.0

    def _verify_date_claim(self, claim_date_str: str, date_range: tuple) -> dict:
        """
        Verify a date claim against the transaction date range.

        Args:
            claim_date_str: The date string from the narrative
            date_range: Tuple of (start_date, end_date) from facts

        Returns:
            Verification result with confidence score
        """
        try:
            # Parse the claimed date
            claimed_date = date_parser.parse(claim_date_str, fuzzy=True)

            # Parse date range (handle string or datetime objects)
            start_date = date_range[0]
            end_date = date_range[1]

            if isinstance(start_date, str):
                start_date = date_parser.parse(start_date)
            if isinstance(end_date, str):
                end_date = date_parser.parse(end_date)

            # Check if claimed date falls within the transaction date range
            if start_date <= claimed_date <= end_date:
                return {
                    "verified": True,
                    "confidence": 1.0,
                    "matched_field": "date_range",
                    "expected_range": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                    "actual": claimed_date.strftime('%Y-%m-%d'),
                    "note": "Date falls within transaction date range",
                }

            # Check if date is close to the range (within 30 days)
            from datetime import timedelta
            buffer_days = timedelta(days=30)

            if (start_date - buffer_days) <= claimed_date <= (end_date + buffer_days):
                return {
                    "verified": True,
                    "confidence": 0.85,
                    "matched_field": "date_range",
                    "expected_range": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                    "actual": claimed_date.strftime('%Y-%m-%d'),
                    "note": "Date is close to transaction date range (within 30 days)",
                }

            # Date is outside the range
            return {
                "verified": False,
                "confidence": 0.3,
                "matched_field": "date_range",
                "expected_range": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                "actual": claimed_date.strftime('%Y-%m-%d'),
                "note": "Date falls outside transaction date range",
            }

        except (ValueError, TypeError) as e:
            # Could not parse the date
            return {
                "verified": False,
                "confidence": 0.5,
                "note": f"Could not parse date: {claim_date_str}",
                "error": str(e),
            }

    def verify_claim(
        self,
        claim: dict,
        facts: dict,
        tolerance: float = 0.01,
    ) -> dict:
        """
        Verify a single claim against known facts.

        Args:
            claim: The claim to verify
            facts: Known facts from database
            tolerance: Allowed tolerance for numerical comparisons

        Returns:
            Verification result with confidence score
        """
        claim_type = claim.get("type")
        claim_value = claim.get("value")

        if claim_type == "number":
            # Check against transaction counts, unique sources, etc.
            for key in ["transaction_count", "unique_sources", "sentence_count"]:
                if key in facts:
                    if abs(facts[key] - claim_value) <= tolerance * max(facts[key], 1):
                        return {
                            "verified": True,
                            "confidence": 1.0,
                            "matched_field": key,
                            "expected": facts[key],
                            "actual": claim_value,
                        }

        elif claim_type == "currency":
            # Check against total amounts
            if "total_amount" in facts:
                expected = facts["total_amount"]
                if abs(expected - claim_value) <= tolerance * max(expected, 1):
                    return {
                        "verified": True,
                        "confidence": 1.0,
                        "matched_field": "total_amount",
                        "expected": expected,
                        "actual": claim_value,
                    }

        elif claim_type == "fincen_code":
            # Verify FinCEN code matches typology
            if "fincen_code" in facts:
                if facts["fincen_code"].lower() == claim_value:
                    return {
                        "verified": True,
                        "confidence": 1.0,
                        "matched_field": "fincen_code",
                        "expected": facts["fincen_code"],
                        "actual": claim_value,
                    }

        elif claim_type == "date":
            # Date verification with actual date parsing and comparison
            if "date_range" in facts:
                date_range = facts["date_range"]
                verification_result = self._verify_date_claim(claim_value, date_range)
                return verification_result

        # Default: unverified or low confidence
        return {
            "verified": False,
            "confidence": 0.5,
            "note": f"Could not verify {claim_type} claim",
        }

    def verify_narrative(
        self,
        narrative: str,
        facts: dict,
    ) -> dict:
        """
        Verify all claims in a narrative.

        Returns:
            {
                "verified_narrative": str,
                "confidence": float,
                "claims_verified": int,
                "claims_total": int,
                "sentence_verifications": dict,
            }
        """
        sentences = [s.strip() for s in narrative.split('.') if s.strip()]
        sentence_verifications = {}
        total_claims = 0
        verified_claims = 0

        for idx, sentence in enumerate(sentences):
            claims = self.extract_claims(sentence)
            sentence_confidence = 1.0
            sentence_results = []

            for claim in claims:
                total_claims += 1
                result = self.verify_claim(claim, facts)
                sentence_results.append(result)

                if result["verified"]:
                    verified_claims += 1
                    sentence_confidence = min(sentence_confidence, result["confidence"])
                else:
                    sentence_confidence = min(sentence_confidence, result["confidence"])

            sentence_verifications[idx] = {
                "sentence": sentence,
                "claims": sentence_results,
                "verified": all(r["verified"] for r in sentence_results) if sentence_results else True,
                "confidence": sentence_confidence,
            }

        overall_confidence = verified_claims / total_claims if total_claims > 0 else 1.0

        return {
            "verified_narrative": narrative,
            "confidence": overall_confidence,
            "claims_verified": verified_claims,
            "claims_total": total_claims,
            "sentence_verifications": sentence_verifications,
        }
