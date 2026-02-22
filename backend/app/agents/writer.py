from sqlalchemy.orm import Session
from typing import Any, Optional
import httpx
from datetime import datetime
import json

from app.config import get_settings

settings = get_settings()


# Constitutional AI Principles for SAR Writing
CONSTITUTIONAL_PRINCIPLES = [
    {
        "principle": "Only state facts supported by transaction data",
        "check": "Ensure every claim has a data source",
        "severity": "CRITICAL",
    },
    {
        "principle": "Do not speculate about customer intent",
        "banned_phrases": ["appears to be", "seems like", "probably", "might be", "clearly trying to"],
        "severity": "HIGH",
    },
    {
        "principle": "Use formal regulatory language",
        "banned_words": ["shady", "sketchy", "weird", "fishy", "bad"],
        "severity": "MEDIUM",
    },
    {
        "principle": "Include specific dates, amounts, and account numbers",
        "severity": "CRITICAL",
    },
    {
        "principle": "Cite FinCEN activity codes where applicable",
        "severity": "HIGH",
    },
]

# SAR Narrative Prompt Template
SAR_NARRATIVE_PROMPT = """You are an expert AML compliance officer writing a Suspicious Activity Report (SAR) narrative.

## CRITICAL REQUIREMENTS:
1. ONLY state facts directly supported by the transaction data provided
2. NEVER speculate about customer intent or motivations
3. Use formal regulatory language throughout
4. Include specific dates, amounts (in INR), and account numbers
5. Reference the FinCEN Activity Code provided
6. Structure the narrative in clear paragraphs

## BANNED PHRASES (never use these):
- "appears to be", "seems like", "probably", "might be", "clearly trying to"
- "shady", "sketchy", "weird", "fishy", "bad"
- Any speculative language about intent

## REGULATORY CONTEXT:
{regulatory_context}

## TRANSACTION FACTS:
{facts_json}

## CLASSIFICATION:
- Typology: {typology}
- FinCEN Activity Code: {fincen_code}
- Indicators: {indicators}

## TASK:
Write a complete SAR narrative (5-7 paragraphs) covering:
1. Subject Identification (name, PAN, account number, review period)
2. Activity Summary (total transactions, amounts, sources)
3. Transaction Details (date ranges, amounts, patterns)
4. Pattern Analysis (why this is suspicious, referencing specific indicators)
5. Conclusion (recommendation to file SAR with regulatory citation)

Write the narrative now:"""


class NarrativeWriterAgent:
    """
    Agent 3: Narrative Writer

    Responsible for:
    - Generating SAR narrative using RAG and LLM
    - Applying Constitutional AI principles
    - Maintaining formal regulatory tone
    """

    def __init__(self, db: Session):
        self.db = db
        self.ollama_url = settings.ollama_base_url
        self.model = settings.ollama_model

    async def generate_narrative(
        self,
        facts: dict[str, Any],
        typology: str,
        fincen_code: str,
        regulatory_context: Optional[dict] = None,
    ) -> str:
        """
        Generate a complete SAR narrative using LLM with RAG context.

        Returns:
            Complete narrative text (5-7 paragraphs)
        """
        # Try LLM-powered generation first
        narrative = await self._generate_with_llm(
            facts, typology, fincen_code, regulatory_context
        )

        # Fallback to template if LLM fails
        if not narrative:
            print("LLM generation failed, falling back to template")
            narrative = self._generate_template_narrative(facts, typology, fincen_code)

        # Apply constitutional checks regardless of generation method
        narrative = self._apply_constitutional_checks(narrative)

        return narrative

    async def _generate_with_llm(
        self,
        facts: dict[str, Any],
        typology: str,
        fincen_code: str,
        regulatory_context: Optional[dict] = None,
    ) -> str:
        """Generate narrative using Ollama LLM."""
        # Build regulatory context string
        reg_context_str = self._format_regulatory_context(regulatory_context)

        # Format facts for the prompt (sanitize sensitive data)
        facts_for_prompt = self._prepare_facts_for_prompt(facts)

        # Get indicators from facts or regulatory context
        indicators = facts.get("patterns", [])
        if regulatory_context and "indicators" in regulatory_context:
            indicators.extend(regulatory_context["indicators"])

        # Build the prompt
        prompt = SAR_NARRATIVE_PROMPT.format(
            regulatory_context=reg_context_str,
            facts_json=json.dumps(facts_for_prompt, indent=2, default=str),
            typology=typology,
            fincen_code=fincen_code,
            indicators=", ".join(indicators[:5]) if indicators else "See pattern analysis",
        )

        # Call the LLM
        response = await self._call_llm(prompt)

        if response:
            # Clean up the response
            response = self._clean_llm_response(response)

        return response

    def _format_regulatory_context(self, regulatory_context: Optional[dict]) -> str:
        """Format regulatory context for the prompt."""
        if not regulatory_context:
            return """- SAR filing required under 31 CFR 1020.320
- File within 30 days of detection
- Include all relevant transaction details
- Document customer identification information"""

        parts = []

        if "fincen_guidance" in regulatory_context:
            parts.append(f"FinCEN Guidance: {regulatory_context['fincen_guidance']}")

        if "filing_requirements" in regulatory_context:
            parts.append("Filing Requirements:")
            for req in regulatory_context["filing_requirements"]:
                parts.append(f"  - {req}")

        if "supporting_regulations" in regulatory_context:
            parts.append("Supporting Regulations:")
            for reg in regulatory_context["supporting_regulations"]:
                parts.append(f"  - {reg}")

        return "\n".join(parts)

    def _prepare_facts_for_prompt(self, facts: dict) -> dict:
        """Prepare facts dict for inclusion in prompt, sanitizing as needed."""
        # Create a copy to avoid modifying the original
        safe_facts = {}

        # Customer info (mask sensitive data partially)
        if "customer" in facts:
            customer = facts["customer"]
            safe_facts["customer"] = {
                "name": customer.get("name", "Unknown"),
                "pan": customer.get("pan", "N/A"),
                "account_number_masked": self._mask_account(customer.get("account_number", "")),
                "occupation": customer.get("occupation", "Not specified"),
            }

        # Transaction statistics
        safe_facts["transaction_count"] = facts.get("transaction_count", 0)
        safe_facts["total_amount_inr"] = facts.get("total_amount", 0)
        safe_facts["unique_sources"] = facts.get("unique_sources", 0)
        safe_facts["date_range"] = facts.get("date_range", (None, None))

        # Patterns detected
        safe_facts["suspicious_patterns"] = facts.get("patterns", [])

        # Alert info
        safe_facts["alert_scenario"] = facts.get("scenario", "Unknown")
        safe_facts["risk_score"] = facts.get("risk_score", 0)

        # Sample transactions (limited for prompt size)
        transactions = facts.get("transactions", [])
        if transactions:
            safe_facts["sample_transactions"] = transactions[:5]

        return safe_facts

    def _mask_account(self, account: str) -> str:
        """Mask account number for privacy."""
        if account and len(account) > 4:
            return f"****{account[-4:]}"
        return account or "N/A"

    def _clean_llm_response(self, response: str) -> str:
        """Clean up LLM response, removing any preamble or meta-text."""
        # Remove common LLM preambles
        preambles_to_remove = [
            "Here is the SAR narrative:",
            "Here's the SAR narrative:",
            "SAR Narrative:",
            "Here is a SAR narrative based on the provided information:",
        ]

        for preamble in preambles_to_remove:
            if response.strip().startswith(preamble):
                response = response.strip()[len(preamble):].strip()

        # Remove any trailing meta-comments
        if "\n\n---" in response:
            response = response.split("\n\n---")[0]

        return response.strip()

    def _generate_template_narrative(
        self,
        facts: dict[str, Any],
        typology: str,
        fincen_code: str,
    ) -> str:
        """
        Fallback template-based narrative generation.
        Used when LLM is unavailable.
        """
        sections = []

        # Section 1: Subject Identification
        sections.append(self._generate_subject_section(facts))

        # Section 2: Activity Summary
        sections.append(self._generate_activity_section(facts))

        # Section 3: Transaction Details
        sections.append(self._generate_transaction_section(facts))

        # Section 4: Pattern Analysis
        sections.append(self._generate_pattern_section(facts, typology, fincen_code))

        # Section 5: Conclusion
        sections.append(self._generate_conclusion_section(typology, fincen_code))

        return "\n\n".join(sections)

    def _generate_subject_section(self, facts: dict) -> str:
        """Generate the subject identification paragraph."""
        customer = facts.get("customer", {})
        name = customer.get("name", "Unknown Subject")
        pan = customer.get("pan", "N/A")
        account = customer.get("account_number", "N/A")

        # Mask account number for privacy
        if account and len(account) > 4:
            account = f"****{account[-4:]}"

        date_range = facts.get("date_range", (None, None))
        if date_range[0] and date_range[1]:
            period = f"{self._format_date(date_range[0])} through {self._format_date(date_range[1])}"
        else:
            period = "the review period"

        return (
            f"Review of account activity for {name} "
            f"(PAN: {pan}), savings account #{account}, "
            f"revealed suspicious transaction patterns during {period}."
        )

    def _generate_activity_section(self, facts: dict) -> str:
        """Generate the activity summary paragraph."""
        txn_count = facts.get("transaction_count", 0)
        total_amount = facts.get("total_amount", 0)
        unique_sources = facts.get("unique_sources", 0)

        # Format amount in Indian style
        formatted_amount = self._format_indian_currency(total_amount)

        parts = [
            f"The subject received {txn_count} separate deposits "
            f"totaling {formatted_amount}"
        ]

        if unique_sources > 1:
            parts.append(f"from {unique_sources} distinct source accounts")

        date_range = facts.get("date_range", (None, None))
        if date_range[0] and date_range[1]:
            start = datetime.fromisoformat(date_range[0]) if isinstance(date_range[0], str) else date_range[0]
            end = datetime.fromisoformat(date_range[1]) if isinstance(date_range[1], str) else date_range[1]
            days = (end - start).days + 1
            parts.append(f"over a {days}-day period")

        return ". ".join(parts) + "."

    def _generate_transaction_section(self, facts: dict) -> str:
        """Generate transaction details paragraph."""
        transactions = facts.get("transactions", [])

        if not transactions:
            return "Transaction details are documented in the attached schedule."

        amounts = [t.get("amount", 0) for t in transactions]
        min_amount = min(amounts) if amounts else 0
        max_amount = max(amounts) if amounts else 0

        section = (
            f"Individual transaction amounts ranged from "
            f"{self._format_indian_currency(min_amount)} to "
            f"{self._format_indian_currency(max_amount)}."
        )

        # Check for outbound transfers
        outbound = [t for t in transactions if t.get("direction") == "OUTBOUND"]
        if outbound:
            outbound_total = sum(t.get("amount", 0) for t in outbound)
            destinations = set(t.get("destination_location") for t in outbound if t.get("destination_location"))

            if destinations:
                section += (
                    f" Subsequently, the subject initiated outbound transfers "
                    f"totaling {self._format_indian_currency(outbound_total)} "
                    f"to {', '.join(destinations)}."
                )

        return section

    def _generate_pattern_section(self, facts: dict, typology: str, fincen_code: str) -> str:
        """Generate pattern analysis paragraph."""
        patterns = facts.get("patterns", [])

        section = (
            f"The transaction pattern is consistent with {typology.lower()} activity "
            f"(FinCEN Activity Code {fincen_code})."
        )

        if patterns:
            section += f" Specifically, the following indicators were identified: "
            section += "; ".join(patterns[:3]) + "."

        # Add context about customer profile if available
        customer = facts.get("customer", {})
        occupation = customer.get("occupation")
        if occupation:
            section += (
                f" The subject's declared occupation is {occupation}, "
                f"which does not readily explain the volume or nature of these transactions."
            )

        return section

    def _generate_conclusion_section(self, typology: str, fincen_code: str) -> str:
        """Generate conclusion paragraph."""
        return (
            f"Based on the totality of circumstances, including the transaction patterns, "
            f"volume, and timing described above, this activity is consistent with "
            f"{typology.lower()} and warrants the filing of this Suspicious Activity Report "
            f"pursuant to 31 CFR 1020.320."
        )

    def _apply_constitutional_checks(self, narrative: str) -> str:
        """Apply Constitutional AI principles to the narrative."""
        # Remove banned phrases
        for principle in CONSTITUTIONAL_PRINCIPLES:
            banned = principle.get("banned_phrases", []) + principle.get("banned_words", [])
            for phrase in banned:
                if phrase.lower() in narrative.lower():
                    # Replace with appropriate alternative
                    narrative = narrative.replace(phrase, "")
                    narrative = narrative.replace(phrase.capitalize(), "")

        # Clean up any double spaces
        while "  " in narrative:
            narrative = narrative.replace("  ", " ")

        return narrative.strip()

    def _format_date(self, date_str: str) -> str:
        """Format date string for narrative."""
        if isinstance(date_str, str):
            try:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return dt.strftime("%B %d, %Y")
            except ValueError:
                return date_str
        return str(date_str)

    def _format_indian_currency(self, amount: float) -> str:
        """Format amount in Indian currency style."""
        if amount >= 10000000:  # 1 crore
            return f"₹{amount/10000000:.2f} crore"
        elif amount >= 100000:  # 1 lakh
            return f"₹{amount/100000:.2f} lakh"
        else:
            return f"₹{amount:,.0f}"

    async def _call_llm(self, prompt: str) -> str:
        """Call Ollama LLM for generation."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.3,  # Low temperature for factual output
                            "top_p": 0.9,
                            "num_predict": 2000,  # Enough for a full narrative
                        },
                    },
                    timeout=120.0,  # Longer timeout for narrative generation
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
                models = response.json().get("models", [])
                return any(m.get("name", "").startswith(self.model.split(":")[0]) for m in models)
        except Exception:
            return False
