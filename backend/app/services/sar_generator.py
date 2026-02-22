from typing import Callable, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import asyncio
from dataclasses import dataclass, field

from app.db import crud
from app.services.audit_trail import AuditTrailService
from app.agents.data_analyst import DataAnalystAgent
from app.agents.compliance import ComplianceAgent
from app.agents.writer import NarrativeWriterAgent
from app.agents.fact_checker import FactCheckerAgent
from app.agents.editor import EditorAgent
from app.knowledge_base.vector_store import get_vector_store


@dataclass
class TokenUsageTracker:
    """Tracks LLM token usage across the pipeline."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    by_agent: dict = field(default_factory=dict)

    def add_usage(self, agent_name: str, prompt: int, completion: int):
        """Add token usage for an agent."""
        self.prompt_tokens += prompt
        self.completion_tokens += completion
        self.total_tokens += prompt + completion
        if agent_name not in self.by_agent:
            self.by_agent[agent_name] = {"prompt": 0, "completion": 0, "total": 0}
        self.by_agent[agent_name]["prompt"] += prompt
        self.by_agent[agent_name]["completion"] += completion
        self.by_agent[agent_name]["total"] += prompt + completion

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total": self.total_tokens,
            "by_agent": self.by_agent,
        }


class SARGeneratorService:
    """
    Orchestrates the multi-agent SAR generation pipeline.

    Pipeline:
    1. Data Analyst - Extract facts from database
    2. Compliance Specialist - Classify typology (LLM-powered)
    3. Narrative Writer - Generate SAR narrative (LLM-powered with RAG)
    4. Fact Checker - Verify all claims
    5. Editor - Polish grammar and style (LLM-powered)
    """

    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditTrailService(db)

        # Initialize agents
        self.data_analyst = DataAnalystAgent(db)
        self.compliance_agent = ComplianceAgent(db)
        self.writer_agent = NarrativeWriterAgent(db)
        self.fact_checker = FactCheckerAgent(db)
        self.editor_agent = EditorAgent(db)
        self.token_tracker = TokenUsageTracker()

        # Initialize vector store for RAG
        self.vector_store = get_vector_store()

    async def generate(
        self,
        alert_id: str,
        sar_id: str,
        on_progress: Optional[Callable[[str, int], None]] = None,
    ) -> dict:
        """
        Run the full SAR generation pipeline.

        Args:
            alert_id: The alert to generate SAR for
            sar_id: Pre-generated SAR ID
            on_progress: Callback for progress updates (agent_name, progress_percent)

        Returns:
            Generated SAR data
        """
        try:
            # Stage 1: Data Analysis (0-20%)
            if on_progress:
                on_progress("data_analyst", 0)

            facts = await self.data_analyst.extract_facts(alert_id)
            self._track_agent_tokens("data_analyst", facts)

            if on_progress:
                on_progress("data_analyst", 20)

            # Stage 2: Compliance Classification (20-40%)
            if on_progress:
                on_progress("compliance", 20)

            typology_result = await self.compliance_agent.classify_typology(facts)
            self._track_agent_tokens("compliance", typology_result)

            # Get regulatory context for the identified typology
            regulatory_context = await self.compliance_agent.get_regulatory_context(
                typology_result["typology"]
            )

            # Get additional RAG context from vector store
            rag_context = self.vector_store.get_rag_context(
                facts=facts,
                typology=typology_result["typology"],
            )

            # Merge regulatory context with RAG context
            if rag_context.get("regulatory_guidance"):
                regulatory_context["rag_guidance"] = rag_context["regulatory_guidance"]

            if on_progress:
                on_progress("compliance", 40)

            # Stage 3: Narrative Generation (40-70%)
            if on_progress:
                on_progress("writer", 40)

            # Generate narrative with LLM and RAG context
            narrative_result = await self.writer_agent.generate_narrative(
                facts=facts,
                typology=typology_result["typology"],
                fincen_code=typology_result["fincen_code"],
                regulatory_context=regulatory_context,  # Pass RAG context to writer
            )
            narrative = narrative_result if isinstance(narrative_result, str) else narrative_result.get("narrative", narrative_result)
            self._track_agent_tokens("writer", narrative_result if isinstance(narrative_result, dict) else {"narrative": narrative_result})

            if on_progress:
                on_progress("writer", 70)

            # Stage 4: Fact Checking (70-90%)
            if on_progress:
                on_progress("fact_checker", 70)

            verification_result = await self.fact_checker.verify_narrative(
                narrative=narrative,
                facts=facts,
                sar_id=sar_id,
            )
            self._track_agent_tokens("fact_checker", verification_result)

            if on_progress:
                on_progress("fact_checker", 90)

            # Stage 5: Editing (90-100%)
            if on_progress:
                on_progress("editor", 90)

            editor_result = await self.editor_agent.polish_narrative(
                narrative=verification_result["verified_narrative"]
            )
            final_narrative = editor_result if isinstance(editor_result, str) else editor_result.get("narrative", editor_result)
            self._track_agent_tokens("editor", editor_result if isinstance(editor_result, dict) else {"narrative": editor_result})

            if on_progress:
                on_progress("editor", 100)

            # Save SAR to database
            sar = crud.create_sar(
                db=self.db,
                alert_id=alert_id,
                narrative=final_narrative,
                typology=typology_result["typology"],
                fincen_code=typology_result["fincen_code"],
                confidence_score=verification_result["confidence"],
            )

            # Override the auto-generated ID with our pre-generated one
            sar.id = sar_id
            self.db.commit()

            # Create audit trail entries
            await self._create_audit_trail(
                sar_id=sar_id,
                facts=facts,
                typology_result=typology_result,
                verification_result=verification_result,
                narrative=final_narrative,
                regulatory_context=regulatory_context,
            )

            return {
                "sar_id": sar_id,
                "narrative": final_narrative,
                "typology": typology_result["typology"],
                "fincen_code": typology_result["fincen_code"],
                "confidence": verification_result["confidence"],
                "token_usage": self.token_tracker.to_dict(),
                "llm_generated": typology_result.get("llm_generated", False),
                "regulatory_context_used": bool(regulatory_context.get("rag_guidance")),
            }

        except Exception as e:
            # Log error and re-raise
            print(f"SAR generation failed: {e}")
            raise

    async def check_llm_status(self) -> dict:
        """Check if LLM services are available."""
        writer_available = await self.writer_agent.check_llm_availability()
        compliance_available = await self.compliance_agent.check_llm_availability()
        editor_available = await self.editor_agent.check_llm_availability()

        return {
            "llm_available": writer_available and compliance_available and editor_available,
            "agents": {
                "writer": writer_available,
                "compliance": compliance_available,
                "editor": editor_available,
            },
            "fallback_mode": not (writer_available and compliance_available and editor_available),
        }

    async def _create_audit_trail(
        self,
        sar_id: str,
        facts: dict,
        typology_result: dict,
        verification_result: dict,
        narrative: str,
        regulatory_context: Optional[dict] = None,
    ):
        """Create audit trail entries for each sentence."""
        sentences = [s.strip() for s in narrative.split(".") if s.strip()]

        for idx, sentence in enumerate(sentences):
            # Log SQL queries used
            if "queries" in facts:
                for query_info in facts["queries"]:
                    crud.create_audit_log(
                        db=self.db,
                        sar_id=sar_id,
                        sentence_index=idx,
                        entry_type="sql_query",
                        data={
                            "query": query_info.get("query"),
                            "results": query_info.get("results", []),
                        },
                        confidence=1.0,
                    )

            # Log fact verification
            if idx in verification_result.get("sentence_verifications", {}):
                verification = verification_result["sentence_verifications"][idx]
                crud.create_audit_log(
                    db=self.db,
                    sar_id=sar_id,
                    sentence_index=idx,
                    entry_type="fact_verification",
                    data={
                        "claim": sentence,
                        "verified": verification.get("verified", True),
                        "confidence": verification.get("confidence", 1.0),
                    },
                    confidence=verification.get("confidence", 1.0),
                )

            # Log LLM generation with actual token usage
            sentence_token_estimate = self._estimate_sentence_tokens(sentence, len(sentences))

            llm_data = {
                "prompt": f"Generate sentence for facts: {facts}",
                "response": sentence,
                "reasoning": f"Generated based on {typology_result['typology']} typology",
                "tokens_used": sentence_token_estimate,
                "llm_generated": typology_result.get("llm_generated", False),
            }

            # Add RAG context info if available
            if regulatory_context and regulatory_context.get("rag_guidance"):
                llm_data["rag_context_used"] = True
                llm_data["regulatory_sources"] = [
                    g.get("title", "Unknown") for g in regulatory_context.get("rag_guidance", [])
                ]

            crud.create_audit_log(
                db=self.db,
                sar_id=sar_id,
                sentence_index=idx,
                entry_type="llm_generation",
                data=llm_data,
                confidence=verification_result.get("confidence", 1.0),
            )

    def _track_agent_tokens(self, agent_name: str, result: dict):
        """
        Track token usage from agent results.
        Extracts token_usage from result if present, otherwise estimates based on content.
        """
        if isinstance(result, dict) and "token_usage" in result:
            usage = result["token_usage"]
            self.token_tracker.add_usage(
                agent_name,
                usage.get("prompt_tokens", 0),
                usage.get("completion_tokens", 0),
            )
        else:
            # Estimate tokens based on content length (roughly 4 chars per token)
            content_str = str(result)
            estimated_tokens = len(content_str) // 4
            # Assume 60% prompt, 40% completion for estimates
            prompt_estimate = int(estimated_tokens * 0.6)
            completion_estimate = int(estimated_tokens * 0.4)
            self.token_tracker.add_usage(agent_name, prompt_estimate, completion_estimate)

    def _estimate_sentence_tokens(self, sentence: str, total_sentences: int) -> dict:
        """
        Estimate token usage for a specific sentence based on tracked totals.
        Distributes the total writer tokens proportionally across sentences.
        """
        writer_tokens = self.token_tracker.by_agent.get("writer", {})
        total_writer_tokens = writer_tokens.get("total", 0)

        if total_sentences > 0 and total_writer_tokens > 0:
            # Distribute tokens based on sentence length relative to average
            sentence_chars = len(sentence)
            per_sentence_tokens = total_writer_tokens // total_sentences
            # Weight by relative sentence length
            sentence_token_estimate = max(1, int(sentence_chars / 4))

            return {
                "prompt_tokens": per_sentence_tokens // 2,
                "completion_tokens": sentence_token_estimate,
                "total": per_sentence_tokens // 2 + sentence_token_estimate,
            }

        # Fallback: estimate based on sentence length
        sentence_tokens = max(1, len(sentence) // 4)
        return {
            "prompt_tokens": sentence_tokens * 2,
            "completion_tokens": sentence_tokens,
            "total": sentence_tokens * 3,
        }
