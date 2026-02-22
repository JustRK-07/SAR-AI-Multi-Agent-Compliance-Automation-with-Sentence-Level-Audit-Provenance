from sqlalchemy.orm import Session
from typing import Any, Optional
import httpx
import json

from app.config import get_settings

settings = get_settings()


# FinCEN SAR Activity Codes
FINCEN_CODES = {
    "structuring": {
        "code": "31a",
        "name": "Structuring",
        "description": "Transactions structured to avoid reporting threshold",
        "indicators": [
            "Multiple transactions below $10,000/₹10 lakh",
            "Consistent patterns of deposits/withdrawals",
            "Transactions by same customer at multiple branches",
        ],
    },
    "layering": {
        "code": "31z",
        "name": "Money Laundering - Layering",
        "description": "Complex transactions to obscure source of funds",
        "indicators": [
            "Rapid movement of funds through multiple accounts",
            "Circular transactions",
            "Shell company involvement",
        ],
    },
    "rapid_movement": {
        "code": "31z",
        "name": "Rapid Fund Movement",
        "description": "Immediate transfer of incoming funds",
        "indicators": [
            "Funds transferred within hours of receipt",
            "No apparent business purpose",
            "Transfers to high-risk jurisdictions",
        ],
    },
    "collection_account": {
        "code": "31z",
        "name": "Collection Account",
        "description": "Account receiving funds from multiple sources",
        "indicators": [
            "Multiple incoming transfers from unrelated parties",
            "Funds consolidated then moved offshore",
            "No legitimate business explanation",
        ],
    },
    "trade_based": {
        "code": "35f",
        "name": "Trade-Based Money Laundering",
        "description": "Over/under invoicing of goods or services",
        "indicators": [
            "Discrepancies in trade documentation",
            "Unusual pricing for goods/services",
            "Third-party payments",
        ],
    },
    "terrorist_financing": {
        "code": "42",
        "name": "Terrorist Financing",
        "description": "Funds supporting terrorist activities",
        "indicators": [
            "Transfers to sanctioned entities",
            "Connections to known terrorist organizations",
            "Unusual patterns in conflict zones",
        ],
    },
    "fraud": {
        "code": "08",
        "name": "Fraud",
        "description": "Fraudulent activity detected",
        "indicators": [
            "Identity theft indicators",
            "Unauthorized transactions",
            "Account takeover patterns",
        ],
    },
}

# LLM Prompt for Typology Classification
TYPOLOGY_CLASSIFICATION_PROMPT = """You are an expert AML compliance analyst specializing in suspicious activity classification.

## TASK:
Analyze the transaction data and classify the suspicious activity typology.

## AVAILABLE TYPOLOGIES:
{typologies_list}

## TRANSACTION DATA:
{transaction_data}

## DETECTED PATTERNS:
{patterns}

## INSTRUCTIONS:
1. Analyze the transaction patterns carefully
2. Select the MOST APPROPRIATE typology from the list above
3. Provide your confidence level (0.0 to 1.0)
4. Explain your reasoning with specific references to the data

## OUTPUT FORMAT (respond in valid JSON only):
{{
    "typology_key": "one of: structuring, layering, rapid_movement, collection_account, trade_based, terrorist_financing, fraud",
    "confidence": 0.0 to 1.0,
    "reasoning": "Detailed explanation referencing specific transaction patterns...",
    "key_indicators": ["indicator 1", "indicator 2", "indicator 3"]
}}

Respond with JSON only, no other text:"""


class ComplianceAgent:
    """
    Agent 2: Compliance Specialist

    Responsible for:
    - Classifying AML typology from transaction patterns
    - Retrieving appropriate FinCEN activity codes
    - Fetching relevant regulatory context
    """

    def __init__(self, db: Session):
        self.db = db
        self.ollama_url = settings.ollama_base_url
        self.model = settings.ollama_model

    async def classify_typology(self, facts: dict[str, Any]) -> dict:
        """
        Classify the suspicious activity typology based on transaction facts.

        Returns:
            {
                "typology": str,
                "fincen_code": str,
                "confidence": float,
                "indicators": list[str],
                "reasoning": str,
            }
        """
        # Try LLM-based classification first
        llm_result = await self._classify_with_llm(facts)

        if llm_result:
            return llm_result

        # Fallback to rule-based classification
        print("LLM classification failed, falling back to rule-based")
        return self._classify_rule_based(facts)

    async def _classify_with_llm(self, facts: dict[str, Any]) -> Optional[dict]:
        """Use LLM for intelligent typology classification."""
        # Build typologies list for prompt
        typologies_list = self._format_typologies_for_prompt()

        # Format transaction data
        transaction_data = self._format_transaction_data(facts)

        # Get patterns
        patterns = facts.get("patterns", [])
        patterns_str = "\n".join(f"- {p}" for p in patterns) if patterns else "No patterns detected"

        # Build prompt
        prompt = TYPOLOGY_CLASSIFICATION_PROMPT.format(
            typologies_list=typologies_list,
            transaction_data=transaction_data,
            patterns=patterns_str,
        )

        # Call LLM
        response = await self._call_llm(prompt)

        if not response:
            return None

        # Parse JSON response
        try:
            result = self._parse_llm_response(response)
            if result:
                return result
        except Exception as e:
            print(f"Failed to parse LLM response: {e}")

        return None

    def _format_typologies_for_prompt(self) -> str:
        """Format available typologies for the LLM prompt."""
        lines = []
        for key, info in FINCEN_CODES.items():
            indicators_str = ", ".join(info["indicators"][:2])
            lines.append(f"- {key}: {info['name']} (Code {info['code']}) - {info['description']}. Indicators: {indicators_str}")
        return "\n".join(lines)

    def _format_transaction_data(self, facts: dict) -> str:
        """Format transaction facts for the LLM prompt."""
        parts = []

        # Alert info
        parts.append(f"Alert Scenario: {facts.get('scenario', 'Unknown')}")
        parts.append(f"Risk Score: {facts.get('risk_score', 0)}")

        # Transaction statistics
        parts.append(f"Transaction Count: {facts.get('transaction_count', 0)}")
        parts.append(f"Total Amount: ₹{facts.get('total_amount', 0):,.0f}")
        parts.append(f"Unique Sources: {facts.get('unique_sources', 0)}")

        # Date range
        date_range = facts.get("date_range", (None, None))
        if date_range[0] and date_range[1]:
            parts.append(f"Date Range: {date_range[0]} to {date_range[1]}")

        # Customer info
        customer = facts.get("customer", {})
        if customer:
            parts.append(f"Customer Occupation: {customer.get('occupation', 'Unknown')}")

        # Sample transactions
        transactions = facts.get("transactions", [])
        if transactions:
            parts.append("\nSample Transactions:")
            for i, txn in enumerate(transactions[:5]):
                parts.append(f"  {i+1}. {txn.get('date', 'N/A')}: ₹{txn.get('amount', 0):,.0f} ({txn.get('type', 'N/A')}) - {txn.get('direction', 'N/A')}")

        return "\n".join(parts)

    def _parse_llm_response(self, response: str) -> Optional[dict]:
        """Parse the JSON response from the LLM."""
        # Try to extract JSON from response
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
            data = json.loads(response)
        except json.JSONDecodeError:
            # Try to find JSON object in response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    data = json.loads(response[start:end])
                except json.JSONDecodeError:
                    return None
            else:
                return None

        # Validate and extract fields
        typology_key = data.get("typology_key", "").lower().replace(" ", "_").replace("-", "_")

        if typology_key not in FINCEN_CODES:
            # Try to match partial
            for key in FINCEN_CODES:
                if key in typology_key or typology_key in key:
                    typology_key = key
                    break
            else:
                typology_key = "layering"  # Default

        typology_info = FINCEN_CODES[typology_key]
        confidence = float(data.get("confidence", 0.7))

        # Combine LLM indicators with standard indicators
        llm_indicators = data.get("key_indicators", [])
        all_indicators = llm_indicators + typology_info["indicators"]

        return {
            "typology": typology_info["name"],
            "fincen_code": typology_info["code"],
            "confidence": min(confidence, 1.0),
            "indicators": all_indicators[:5],
            "reasoning": data.get("reasoning", "Classification based on transaction pattern analysis."),
            "description": typology_info["description"],
            "llm_generated": True,
        }

    def _classify_rule_based(self, facts: dict[str, Any]) -> dict:
        """
        Fallback rule-based classification when LLM is unavailable.
        """
        scenario = facts.get("scenario", "").lower()
        patterns = facts.get("patterns", [])
        transaction_count = facts.get("transaction_count", 0)
        unique_sources = facts.get("unique_sources", 0)

        # Determine typology based on scenario and patterns
        typology_scores = {}

        # Check for structuring
        if "structuring" in scenario.lower():
            typology_scores["structuring"] = 0.9

        for pattern in patterns:
            pattern_lower = pattern.lower()

            if "structuring" in pattern_lower or "threshold" in pattern_lower:
                typology_scores["structuring"] = typology_scores.get("structuring", 0) + 0.3

            if "rapid" in pattern_lower or "movement" in pattern_lower:
                typology_scores["rapid_movement"] = typology_scores.get("rapid_movement", 0) + 0.3
                typology_scores["layering"] = typology_scores.get("layering", 0) + 0.2

            if "collection" in pattern_lower or "multiple sources" in pattern_lower:
                typology_scores["collection_account"] = typology_scores.get("collection_account", 0) + 0.3

            if "offshore" in pattern_lower or "high-risk" in pattern_lower:
                typology_scores["layering"] = typology_scores.get("layering", 0) + 0.3

        # Additional heuristics
        if unique_sources > 10:
            typology_scores["collection_account"] = typology_scores.get("collection_account", 0) + 0.2

        if transaction_count > 30:
            typology_scores["structuring"] = typology_scores.get("structuring", 0) + 0.1

        # Select highest scoring typology
        if not typology_scores:
            typology_scores["layering"] = 0.5  # Default

        best_typology = max(typology_scores, key=typology_scores.get)
        confidence = min(typology_scores[best_typology], 1.0)

        # Get typology details
        typology_info = FINCEN_CODES.get(best_typology, FINCEN_CODES["layering"])

        # Build reasoning
        reasoning = self._build_reasoning(facts, best_typology, patterns)

        return {
            "typology": typology_info["name"],
            "fincen_code": typology_info["code"],
            "confidence": confidence,
            "indicators": typology_info["indicators"],
            "reasoning": reasoning,
            "description": typology_info["description"],
            "llm_generated": False,
        }

    def _build_reasoning(self, facts: dict, typology: str, patterns: list[str]) -> str:
        """Build explanation for typology classification."""
        reasoning_parts = []

        reasoning_parts.append(f"Alert scenario: {facts.get('scenario', 'Unknown')}")

        if patterns:
            reasoning_parts.append(f"Detected patterns: {', '.join(patterns[:3])}")

        reasoning_parts.append(f"Transaction count: {facts.get('transaction_count', 0)}")
        reasoning_parts.append(f"Unique sources: {facts.get('unique_sources', 0)}")

        if facts.get("total_amount"):
            reasoning_parts.append(f"Total amount: ₹{facts['total_amount']:,.0f}")

        reasoning_parts.append(f"Classification: {typology.replace('_', ' ').title()}")

        return ". ".join(reasoning_parts)

    async def get_regulatory_context(self, typology: str) -> dict:
        """
        Retrieve regulatory guidelines for a given typology.
        """
        typology_key = typology.lower().replace(" ", "_").replace("-", "_")

        # Handle common variations
        if "money_laundering" in typology_key or "layering" in typology_key:
            typology_key = "layering"
        elif "structur" in typology_key:
            typology_key = "structuring"

        typology_info = FINCEN_CODES.get(typology_key, FINCEN_CODES["layering"])

        return {
            "fincen_guidance": typology_info["description"],
            "indicators": typology_info["indicators"],
            "filing_requirements": [
                "File SAR within 30 days of detection",
                "Include all relevant transaction details",
                "Document customer identification information",
                "Describe the suspicious activity clearly",
            ],
            "supporting_regulations": [
                "31 CFR 1020.320 - SAR filing requirements",
                "FinCEN Advisory FIN-2023-A001",
                "FATF Recommendation 20 - Suspicious Transaction Reporting",
            ],
        }

    async def _call_llm(self, prompt: str) -> str:
        """Call Ollama LLM for classification."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.1,  # Very low for consistent classification
                            "top_p": 0.9,
                            "num_predict": 500,
                        },
                    },
                    timeout=60.0,
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
