"""
Re:Nova — Stage 1 agentic questionnaire engine.

Drives a natural conversation that covers all 21 Stage 1 questions,
silently records answers via tool calls, and generates both outputs
when complete:
  - Certification Relevance Map  (brand-facing)
  - Greenwashing Risk Assessment (internal only)
"""
from __future__ import annotations
import json
import logging
from typing import Optional

import anthropic

from .models import Session, Message, MessageRole, SessionStatus, QuestionAnswer
from .tools import ALL_TOOLS
from .prompts import SYSTEM_PROMPT, context_hint
from .framework_matcher import match_frameworks
from .greenwashing import run_greenwashing_check, check_answer_for_flags

log = logging.getLogger("renova.questionnaire")


class Stage1Engine:
    """
    Manages the agentic Stage 1 intake session.

    Usage:
        engine = Stage1Engine(api_key="...")
        session = engine.new_session()
        reply = engine.chat(session, "Hello, I'm Sabiha from AkaarDesign")
        # keep calling engine.chat() until session.status == COMPLETE
    """

    def __init__(self, api_key: str, model: str = "claude-opus-4-5"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model   = model

    # ── Public API ────────────────────────────────────────────────────────────

    def new_session(self) -> Session:
        return Session()

    def chat(self, session: Session, user_message: str) -> str:
        """
        Send a user message, get a reply, process any tool calls.
        Returns the assistant's reply text.
        Mutates `session` in-place.
        """
        if session.status != SessionStatus.ACTIVE:
            return "This assessment session is already complete. Thank you for participating."

        session.add_message(MessageRole.USER, user_message)

        # Inject progress hint into system context
        unanswered = session.unanswered_question_ids
        hint = context_hint(unanswered, session.questions_answered)
        system = SYSTEM_PROMPT + f"\n\n[INTERNAL PROGRESS NOTE — NOT SHOWN TO BRAND]: {hint}"

        reply = self._run_turn(session, system)
        session.add_message(MessageRole.ASSISTANT, reply)
        return reply

    # ── Internal turn runner ──────────────────────────────────────────────────

    def _run_turn(self, session: Session, system: str) -> str:
        """
        Run one turn of the agentic loop (handles tool calls recursively).
        Returns the final visible text response.
        """
        messages = session.conversation_history

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system,
            tools=ALL_TOOLS,
            messages=messages
        )

        # Agentic loop: keep processing tool calls until we get a final text response
        while response.stop_reason == "tool_use":
            tool_results = []

            for block in response.content:
                if block.type == "tool_use":
                    result = self._handle_tool(session, block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })

            # Add the assistant turn and tool results to continue
            messages = messages + [
                {"role": "assistant", "content": response.content},
                {"role": "user",      "content": tool_results}
            ]

            # Check if stage is now complete (complete_stage1 was called)
            if session.status == SessionStatus.COMPLETE:
                # Generate a final closing message then stop
                break

            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=system,
                tools=ALL_TOOLS,
                messages=messages
            )

        # Extract the text from the final response
        text_parts = [
            block.text for block in response.content
            if hasattr(block, "text") and block.text
        ]
        return " ".join(text_parts) if text_parts else ""

    # ── Tool handlers ─────────────────────────────────────────────────────────

    def _handle_tool(self, session: Session, tool_name: str, args: dict) -> str:
        """Dispatch a tool call and return a JSON string result."""
        try:
            if tool_name == "record_answer":
                return self._tool_record_answer(session, args)
            elif tool_name == "flag_greenwashing":
                return self._tool_flag_greenwashing(session, args)
            elif tool_name == "complete_stage1":
                return self._tool_complete_stage1(session, args)
            else:
                log.warning("Unknown tool: %s", tool_name)
                return json.dumps({"status": "error", "message": f"Unknown tool: {tool_name}"})
        except Exception as exc:
            log.exception("Tool %s failed", tool_name)
            return json.dumps({"status": "error", "message": str(exc)})

    def _tool_record_answer(self, session: Session, args: dict) -> str:
        question_id = args.get("question_id", "")
        raw_answer  = args.get("raw_answer", "")
        structured  = args.get("structured", {})

        if not question_id or not raw_answer:
            return json.dumps({"status": "error", "message": "question_id and raw_answer are required"})

        session.record_answer(question_id, raw_answer, structured)

        # Pull any brand_name out of structured and cache in facts
        if "brand_name" in structured and structured["brand_name"]:
            session.facts["brand_name"] = structured["brand_name"]

        # Merge all structured fields into session.facts for easy access
        for k, v in structured.items():
            if v is not None and v != "" and v != []:
                session.facts[k] = v

        # Real-time greenwashing check
        rt_flags = check_answer_for_flags(session, question_id, raw_answer)
        if rt_flags:
            if session.greenwashing_assessment is None:
                from .models import GreenwashingRiskAssessment
                session.greenwashing_assessment = GreenwashingRiskAssessment()
            session.greenwashing_assessment.flags.extend(rt_flags)
            session.greenwashing_assessment.compute_overall_risk()
            log.info("Real-time flags raised for %s: %s", question_id,
                     [f.priority for f in rt_flags])

        log.info("Recorded answer for %s (%d/%d)", question_id,
                 session.questions_answered, 21)

        return json.dumps({
            "status": "ok",
            "question_id": question_id,
            "questions_answered": session.questions_answered,
            "questions_remaining": 21 - session.questions_answered,
        })

    def _tool_flag_greenwashing(self, session: Session, args: dict) -> str:
        from .models import GreenwashingFlag, GreenwashingRiskAssessment, FlagPriority, ClaimStatus

        priority_map = {
            "critical": FlagPriority.CRITICAL,
            "moderate": FlagPriority.MODERATE,
            "low":      FlagPriority.LOW,
        }
        priority = priority_map.get(args.get("priority", "moderate").lower(), FlagPriority.MODERATE)

        flag = GreenwashingFlag(
            question_id=args.get("question_id", ""),
            claim=args.get("claim", ""),
            flag_message=args.get("flag_message", ""),
            priority=priority
        )

        if session.greenwashing_assessment is None:
            session.greenwashing_assessment = GreenwashingRiskAssessment()

        # De-duplicate: don't add same (question_id, claim) twice
        existing = {(f.question_id, f.claim) for f in session.greenwashing_assessment.flags}
        if (flag.question_id, flag.claim) not in existing:
            session.greenwashing_assessment.flags.append(flag)
            session.greenwashing_assessment.compute_overall_risk()

        log.info("Greenwashing flag logged: [%s] %s", priority.value, flag.claim)
        return json.dumps({"status": "ok", "flag_priority": priority.value})

    def _tool_complete_stage1(self, session: Session, args: dict) -> str:
        """
        Claude calls this when all 21 questions have been answered.
        Generates both Stage 1 outputs and marks the session complete.
        """
        # ── 1. Generate Certification Relevance Map ──
        brand_name = session.facts.get("brand_name")
        relevance_map = match_frameworks(session, brand_name=brand_name)
        session.relevance_map = relevance_map

        # ── 2. Run full greenwashing check (augments any real-time flags) ──
        full_assessment = run_greenwashing_check(session)

        # Merge: if we already have flags from real-time checks, merge them
        if session.greenwashing_assessment:
            existing_keys = {(f.question_id, f.claim) for f in session.greenwashing_assessment.flags}
            for flag in full_assessment.flags:
                if (flag.question_id, flag.claim) not in existing_keys:
                    session.greenwashing_assessment.flags.append(flag)
            session.greenwashing_assessment.compute_overall_risk()
            if full_assessment.analyst_notes:
                session.greenwashing_assessment.analyst_notes = full_assessment.analyst_notes
        else:
            session.greenwashing_assessment = full_assessment

        # ── 3. Mark session complete ──
        session.status = SessionStatus.COMPLETE

        # Store closing context in facts for any downstream display
        session.facts["closing_message"]  = args.get("closing_message", "")
        session.facts["strengths_observed"] = args.get("strengths_observed", [])
        session.facts["areas_to_prepare"]   = args.get("areas_to_prepare", [])

        log.info(
            "Stage 1 complete for session %s — %d relevant frameworks, risk=%s",
            session.id,
            relevance_map.relevant_count,
            session.greenwashing_assessment.overall_risk.value
        )

        return json.dumps({
            "status": "complete",
            "relevant_frameworks": relevance_map.relevant_count,
            "greenwashing_risk": session.greenwashing_assessment.overall_risk.value,
            "flag_count": len(session.greenwashing_assessment.flags),
        })

    # ── Report formatters ─────────────────────────────────────────────────────

    def format_relevance_map(self, session: Session) -> str:
        """
        Format the Certification Relevance Map as a readable text report
        for the brand-facing output.
        """
        rm = session.relevance_map
        if not rm:
            return "Certification Relevance Map not yet generated."

        brand = rm.brand_name or "Your Brand"
        lines = [
            f"# Re:Nova Certification Relevance Map",
            f"## {brand}",
            f"Generated: {rm.generated_at.strftime('%Y-%m-%d')}",
            "",
            "---",
            "",
            f"## Summary",
            rm.analyst_summary,
            "",
            f"---",
            "",
            f"## Relevant Frameworks ({rm.relevant_count})",
            "",
        ]
        for i, fw in enumerate(rm.relevant_frameworks, 1):
            lines.append(f"### {i}. {fw.name} ({fw.acronym})")
            lines.append(fw.reason)
            lines.append("")

        lines += [
            "---",
            "",
            f"## Not Applicable ({len(rm.excluded_frameworks)})",
            "",
            "The following frameworks have been excluded based on your responses:",
            "",
        ]
        for fw in rm.excluded_frameworks:
            lines.append(f"- **{fw.acronym}** — {fw.reason}")

        lines += ["", "---", "", "_This map was generated from your Stage 1 intake responses.",
                  "It is subject to analyst review before your Re:Nova profile goes live._"]

        return "\n".join(lines)

    def format_greenwashing_assessment(self, session: Session) -> str:
        """
        Format the Greenwashing Risk Assessment as an internal analyst report.
        NOT shared with the brand directly.
        """
        ga = session.greenwashing_assessment
        if not ga:
            return "Greenwashing assessment not yet generated."

        brand = session.facts.get("brand_name", "Unknown Brand")
        risk_emoji = {"green": "🟢", "amber": "🟡", "red": "🔴"}.get(ga.overall_risk.value, "⚪")

        lines = [
            f"# Re:Nova Internal Greenwashing Risk Assessment",
            f"## {brand}",
            f"**Overall Risk: {risk_emoji} {ga.overall_risk.value.upper()}**",
            "",
            "---",
            "",
            f"## Analyst Notes",
            ga.analyst_notes,
            "",
        ]

        if ga.flags:
            lines += [
                "---",
                "",
                f"## Flags ({len(ga.flags)})",
                "",
            ]
            for flag in sorted(ga.flags, key=lambda f: {"critical": 0, "moderate": 1, "low": 2}[f.priority.value]):
                p_emoji = {"critical": "🔴", "moderate": "🟡", "low": "🔵"}.get(flag.priority.value, "⚪")
                lines.append(f"### {p_emoji} [{flag.priority.value.upper()}] {flag.claim}")
                lines.append(f"- Question: {flag.question_id}")
                lines.append(f"- Issue: {flag.flag_message}")
                lines.append(f"- Status: {flag.status.value}")
                lines.append("")

        lines += [
            "---",
            "",
            "_Internal use only. Not shared with brand until analyst review is complete._"
        ]

        return "\n".join(lines)
