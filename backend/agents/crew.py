"""
agents/crew.py — CrewAI Orchestrator.

Wires the three agents (Reader → Analyzer → Structurer) into a
sequential CrewAI pipeline and exposes a single `run()` method.
"""

import logging
from typing import Any

from crewai import Crew, Process

from agents.email_reader import EmailReaderAgent
from agents.analyzer import AnalyzerAgent
from agents.structurer import StructurerAgent

logger = logging.getLogger(__name__)


class EmailIntelligenceCrew:
    """
    Orchestrates the three-agent CrewAI pipeline:

    1. EmailReaderAgent  — cleans and normalizes raw email text
    2. AnalyzerAgent     — calls Gemini for summary / category / priority
    3. StructurerAgent   — produces a validated JSON-ready dict

    Usage:
        crew = EmailIntelligenceCrew()
        result = crew.run(raw_email_dict)
    """

    def __init__(self):
        self.reader_agent = EmailReaderAgent()
        self.analyzer_agent = AnalyzerAgent()
        self.structurer_agent = StructurerAgent()

    def run(self, raw_email: dict[str, Any]) -> dict[str, str]:
        """
        Execute the full agent pipeline on a single raw email.

        Pipeline:
            Step 1 — Reader:     Clean raw email text
            Step 2 — Analyzer:   LLM-based analysis (Gemini)
            Step 3 — Structurer: Produce final structured record

        Args:
            raw_email: Dict with sender, subject, body fields.

        Returns:
            Structured email dict: sender, subject, summary, category, priority.

        Raises:
            ValueError: If the email dict is missing required fields.
            Exception: Propagated from agent failures.
        """
        subject = raw_email.get("subject", "(No Subject)")
        logger.info(f"Starting CrewAI pipeline for: '{subject}'")

        # ── Step 1: Clean email text ───────────────────────────────────
        reader_task = self.reader_agent.create_task(raw_email)

        # ── Step 2: Analyze with Ollama ────────────────────────────────
        # We call analyze() directly here so the LLM call happens within
        # the crew context, then pass the result as context to the task.
        analysis = self.analyzer_agent.analyze(raw_email)
        analyzer_task = self.analyzer_agent.create_task(
            raw_email.get("body", ""), raw_email
        )

        # ── Step 3: Structure the output ───────────────────────────────
        structurer_task = self.structurer_agent.create_task(raw_email, analysis)

        # ── Assemble and Run Crew ──────────────────────────────────────
        crew = Crew(
            agents=[
                self.reader_agent.agent,
                self.analyzer_agent.agent,
                self.structurer_agent.agent,
            ],
            tasks=[reader_task, analyzer_task, structurer_task],
            process=Process.sequential,  # Agents run in order
            verbose=True,
        )

        try:
            crew.kickoff()
            logger.info(f"CrewAI pipeline complete for: '{subject}'")
        except Exception as e:
            logger.error(f"CrewAI pipeline error for '{subject}': {e}")
            # Continue with what we have — analysis was already done
            # before crew kickoff; the structurer can still produce output.

        # Final structured result using the direct structurer (reliable)
        structured = self.structurer_agent.structure(raw_email, analysis)
        return structured
