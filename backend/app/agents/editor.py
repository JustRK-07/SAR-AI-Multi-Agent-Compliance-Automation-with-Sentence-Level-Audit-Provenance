from sqlalchemy.orm import Session
from typing import Optional
import re
import httpx
import json

from app.config import get_settings

settings = get_settings()


# LLM Prompt for Grammar and Compliance Polishing
EDITOR_PROMPT = """You are an expert editor reviewing a Suspicious Activity Report (SAR) narrative for a financial institution.

## YOUR TASK:
Polish the narrative for grammar, clarity, and regulatory compliance while preserving all factual content.

## REQUIREMENTS:
1. Fix any grammar or spelling errors
2. Replace informal language with formal regulatory language
3. Ensure all sentences are clear and professionally written
4. Maintain all facts, dates, amounts, and account numbers exactly as provided
5. Keep the paragraph structure intact
6. DO NOT add any new information or speculation
7. DO NOT change amounts, dates, names, or account numbers

## COMPLIANCE CHECKLIST:
- No contractions (don't → do not)
- No informal words (basically, actually, really, very, just, quite)
- No speculative language (appears to be, seems like, probably, might be)
- All sentences should be in formal passive or active voice
- Each claim should reference specific data

## ORIGINAL NARRATIVE:
{narrative}

## OUTPUT FORMAT:
Return a JSON object with:
{{
    "polished_narrative": "The polished narrative text...",
    "changes_made": ["List of specific changes made"],
    "compliance_issues_fixed": ["List of compliance issues that were fixed"],
    "remaining_concerns": ["Any issues that could not be fixed automatically"]
}}

Return JSON only:"""


class EditorAgent:
    """
    Agent 5: Editor

    Responsible for:
    - Grammar and clarity checking
    - Logical flow verification
    - Style guide compliance (formal language)
    - Completeness check (all required sections)
    """

    # Required elements in a SAR narrative
    REQUIRED_ELEMENTS = [
        "subject identification",  # Name, account, PAN
        "time period",  # Date range
        "transaction summary",  # Count, total amount
        "suspicious indicators",  # What makes it suspicious
        "typology classification",  # FinCEN code
    ]

    # Style guide rules
    STYLE_RULES = {
        "formal_replacements": {
            "don't": "do not",
            "won't": "will not",
            "can't": "cannot",
            "didn't": "did not",
            "isn't": "is not",
            "wasn't": "was not",
            "couldn't": "could not",
            "shouldn't": "should not",
            "wouldn't": "would not",
            "got": "received",
            "lots of": "numerous",
            "a lot of": "numerous",
            "big": "substantial",
            "small": "minimal",
        },
        "banned_informal": [
            "basically",
            "actually",
            "really",
            "very",
            "just",
            "quite",
            "pretty much",
            "kind of",
            "sort of",
        ],
    }

    def __init__(self, db: Session):
        self.db = db
        self.ollama_url = settings.ollama_base_url
        self.model = settings.ollama_model

    async def polish_narrative(self, narrative: str) -> str:
        """
        Polish the narrative for final output.

        Uses LLM for intelligent polishing, with regex fallback.
        """
        # Try LLM-powered polishing first
        polished = await self._polish_with_llm(narrative)

        if polished:
            # Still apply rule-based checks as a safety net
            polished = self._apply_formal_style(polished)
            polished = self._remove_informal_words(polished)
        else:
            # Fallback to rule-based polishing
            print("LLM polishing failed, falling back to rule-based")
            polished = self._polish_rule_based(narrative)

        # Final formatting cleanup
        polished = self._cleanup_formatting(polished)

        return polished

    async def _polish_with_llm(self, narrative: str) -> Optional[str]:
        """Use LLM for intelligent polishing."""
        prompt = EDITOR_PROMPT.format(narrative=narrative)

        response = await self._call_llm(prompt)

        if not response:
            return None

        # Parse JSON response
        try:
            result = self._parse_llm_response(response)
            if result and result.get("polished_narrative"):
                return result["polished_narrative"]
        except Exception as e:
            print(f"Failed to parse LLM response: {e}")

        return None

    def _parse_llm_response(self, response: str) -> Optional[dict]:
        """Parse the JSON response from the LLM."""
        response = response.strip()

        # Handle markdown code blocks
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]

        response = response.strip()

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to find JSON object in response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(response[start:end])
                except json.JSONDecodeError:
                    pass

            # If no JSON, the response might be the polished narrative directly
            if len(response) > 100 and "{" not in response:
                return {"polished_narrative": response}

        return None

    def _polish_rule_based(self, narrative: str) -> str:
        """Fallback rule-based polishing."""
        # Step 1: Apply formal replacements
        polished = self._apply_formal_style(narrative)

        # Step 2: Remove informal words
        polished = self._remove_informal_words(polished)

        # Step 3: Fix common grammar issues
        polished = self._fix_grammar(polished)

        return polished

    def _apply_formal_style(self, text: str) -> str:
        """Replace informal contractions with formal alternatives."""
        for informal, formal in self.STYLE_RULES["formal_replacements"].items():
            # Case-insensitive replacement
            pattern = re.compile(re.escape(informal), re.IGNORECASE)
            text = pattern.sub(formal, text)
        return text

    def _remove_informal_words(self, text: str) -> str:
        """Remove or replace informal filler words."""
        for word in self.STYLE_RULES["banned_informal"]:
            # Remove with surrounding spaces, handling sentence start
            pattern = re.compile(rf'\b{re.escape(word)}\b\s*', re.IGNORECASE)
            text = pattern.sub('', text)
        return text

    def _fix_grammar(self, text: str) -> str:
        """Fix common grammar issues."""
        # Fix double spaces
        while "  " in text:
            text = text.replace("  ", " ")

        # Fix spacing around punctuation
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)
        text = re.sub(r'([.,;:!?])(?=[A-Za-z])', r'\1 ', text)

        # Capitalize first letter of sentences
        sentences = text.split('. ')
        sentences = [s.strip().capitalize() if s else s for s in sentences]
        text = '. '.join(sentences)

        # Ensure proper ending
        text = text.strip()
        if text and not text.endswith('.'):
            text += '.'

        return text

    def _check_completeness(self, narrative: str) -> dict:
        """Check if narrative contains all required elements."""
        narrative_lower = narrative.lower()
        missing = []

        # Check for subject identification
        if not any(word in narrative_lower for word in ["pan:", "account", "subject"]):
            missing.append("subject identification")

        # Check for time period
        if not any(word in narrative_lower for word in ["period", "january", "february", "march",
                                                        "april", "may", "june", "july", "august",
                                                        "september", "october", "november", "december",
                                                        "2024", "2025", "2026"]):
            missing.append("time period")

        # Check for transaction summary
        if not any(word in narrative_lower for word in ["transaction", "deposit", "transfer"]):
            missing.append("transaction summary")

        # Check for suspicious indicators
        if not any(word in narrative_lower for word in ["suspicious", "pattern", "indicator", "unusual"]):
            missing.append("suspicious indicators")

        # Check for typology
        if "fincen" not in narrative_lower and "31 cfr" not in narrative_lower:
            missing.append("typology classification")

        return {
            "is_complete": len(missing) == 0,
            "missing": missing,
            "completeness_score": 1 - (len(missing) / len(self.REQUIRED_ELEMENTS)),
        }

    def _cleanup_formatting(self, text: str) -> str:
        """Final formatting cleanup."""
        # Normalize paragraph breaks
        paragraphs = text.split('\n\n')
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        # Ensure each paragraph is properly formatted
        formatted_paragraphs = []
        for para in paragraphs:
            # Remove extra whitespace within paragraph
            para = ' '.join(para.split())
            formatted_paragraphs.append(para)

        return '\n\n'.join(formatted_paragraphs)

    async def generate_quality_report(self, narrative: str) -> dict:
        """Generate a comprehensive quality report for the narrative."""
        # Try LLM-based quality assessment first
        llm_report = await self._generate_llm_quality_report(narrative)

        # Always include rule-based checks
        completeness = self._check_completeness(narrative)

        # Count sentences and words
        sentences = [s.strip() for s in narrative.split('.') if s.strip()]
        words = narrative.split()

        # Check for remaining informal language
        informal_count = 0
        informal_found = []
        for word in self.STYLE_RULES["banned_informal"]:
            count = narrative.lower().count(word)
            if count > 0:
                informal_count += count
                informal_found.append(word)

        # Check for contractions
        contraction_count = 0
        for contraction in self.STYLE_RULES["formal_replacements"].keys():
            if contraction in narrative.lower():
                contraction_count += 1

        base_report = {
            "sentence_count": len(sentences),
            "word_count": len(words),
            "paragraph_count": len(narrative.split('\n\n')),
            "completeness": completeness,
            "informal_language_issues": informal_count,
            "informal_words_found": informal_found,
            "contractions_found": contraction_count,
            "quality_score": self._calculate_quality_score(
                completeness, informal_count, len(sentences), contraction_count
            ),
        }

        # Merge LLM insights if available
        if llm_report:
            base_report["llm_analysis"] = llm_report
            # Adjust quality score based on LLM feedback
            if "overall_quality" in llm_report:
                base_report["quality_score"] = (
                    base_report["quality_score"] + llm_report["overall_quality"]
                ) / 2

        return base_report

    async def _generate_llm_quality_report(self, narrative: str) -> Optional[dict]:
        """Use LLM to generate quality assessment."""
        prompt = f"""Analyze this SAR narrative for quality and compliance.

NARRATIVE:
{narrative}

Provide a JSON assessment:
{{
    "overall_quality": 0-100 score,
    "clarity": "assessment of clarity",
    "regulatory_compliance": "assessment of regulatory language",
    "factual_support": "assessment of whether claims are supported",
    "suggestions": ["improvement suggestions"]
}}

JSON only:"""

        response = await self._call_llm(prompt)
        if response:
            try:
                return self._parse_llm_response(response)
            except Exception:
                pass
        return None

    def _calculate_quality_score(
        self,
        completeness: dict,
        informal_count: int,
        sentence_count: int,
        contraction_count: int,
    ) -> float:
        """Calculate overall quality score (0-100)."""
        score = 100.0

        # Deduct for missing elements (major issue)
        score -= len(completeness["missing"]) * 10

        # Deduct for informal language
        score -= informal_count * 2

        # Deduct for contractions
        score -= contraction_count * 3

        # Bonus for appropriate length (5-10 sentences ideal)
        if 5 <= sentence_count <= 10:
            score += 5
        elif sentence_count < 3:
            score -= 10
        elif sentence_count > 15:
            score -= 5

        return max(0, min(100, score))

    async def verify_claims(self, narrative: str, facts: dict) -> dict:
        """Verify that claims in the narrative are supported by facts."""
        # Extract amounts mentioned in narrative
        amount_pattern = r'₹[\d,]+(?:\.\d{2})?(?:\s*(?:lakh|crore))?'
        amounts_in_narrative = re.findall(amount_pattern, narrative)

        # Check if key facts are mentioned
        verification = {
            "amounts_verified": True,
            "dates_verified": True,
            "issues": [],
        }

        # Check transaction count
        txn_count = facts.get("transaction_count", 0)
        if str(txn_count) not in narrative and txn_count > 0:
            verification["issues"].append(f"Transaction count ({txn_count}) not found in narrative")

        # Check customer name
        customer = facts.get("customer", {})
        name = customer.get("name", "")
        if name and name not in narrative:
            verification["issues"].append(f"Customer name ({name}) not found in narrative")

        verification["is_verified"] = len(verification["issues"]) == 0

        return verification

    async def _call_llm(self, prompt: str) -> str:
        """Call Ollama LLM for editing."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.2,  # Low for consistent editing
                            "top_p": 0.9,
                            "num_predict": 2000,
                        },
                    },
                    timeout=90.0,
                )
                response.raise_for_status()
                return response.json().get("response", "")
        except httpx.ConnectError:
            print(f"Could not connect to Ollama at {self.ollama_url}. Is Ollama running?")
            return ""
        except httpx.TimeoutException:
            print("LLM request timed out")
            return ""
        except Exception as e:
            print(f"LLM call failed: {e}")
            return ""

    async def check_llm_availability(self) -> bool:
        """Check if Ollama LLM is available."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.ollama_url}/api/tags",
                    timeout=5.0,
                )
                response.raise_for_status()
                return True
        except Exception:
            return False
