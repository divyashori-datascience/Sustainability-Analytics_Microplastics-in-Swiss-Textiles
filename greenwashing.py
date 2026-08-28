"""
Re:Nova — Greenwashing Risk Assessment engine.

Implements the flag logic from the Re:Nova methodology:
- Cross-checks each public claim (O-1.4) against supporting evidence in other answers
- Raises flags at Critical / Moderate / Low priority
- Computes an overall risk rating: Green / Amber / Red
"""
from __future__ import annotations
from .models import (
    Session, GreenwashingFlag, GreenwashingRiskAssessment,
    FlagPriority, ClaimStatus, OverallRisk
)


def _get(session: Session, qid: str) -> str:
    ans = session.answers.get(qid)
    return (ans.raw_answer or "").lower() if ans else ""

def _claims(session: Session) -> str:
    return _get(session, "O-1.4")


def run_greenwashing_check(session: Session) -> GreenwashingRiskAssessment:
    """
    Run the full greenwashing cross-check for a completed Stage 1 session.
    Returns a GreenwashingRiskAssessment for internal use.
    """
    assessment = GreenwashingRiskAssessment()
    claims_text = _claims(session)

    if not claims_text or claims_text in ("none", "no claims", "n/a", ""):
        assessment.overall_risk = OverallRisk.GREEN
        assessment.analyst_notes = "Brand makes no public sustainability claims — no greenwashing risk to assess."
        return assessment

    # ── 1. CRITICAL: Child / forced labour ───────────────────────────────────
    labour_answer = _get(session, "O-3.4")
    # Positive answer: confirmed absence of child/forced labour — no flag
    # Negative trigger: brand answers "no", "I'm unsure", "we cannot confirm"
    labour_confirmed = any(x in labour_answer for x in
                           ["yes", "confirmed", "certif", "audit", "no child", "no forced"])
    if not labour_confirmed:
        assessment.flags.append(GreenwashingFlag(
            question_id="O-3.4",
            claim="Labour rights — child/forced labour",
            flag_message="Brand cannot confirm absence of child or forced labour. Platform access blocked pending analyst review.",
            priority=FlagPriority.CRITICAL,
            status=ClaimStatus.UNSUBSTANTIATED
        ))

    # ── 2. CRITICAL / Moderate: Wages below minimum despite ethical claims ────
    wage_answer = _get(session, "O-3.3")
    ethical_claims = any(x in claims_text for x in
                         ["ethical", "fair trade", "fair wage", "artisan", "living wage"])
    # Wage confirmed if answer is affirmative — "yes", "confirmed", "above", "exceed", etc.
    wage_confirmed = any(x in wage_answer for x in
                         ["yes", "confirmed", "certif", "above", "more than", "exceed", "higher"])
    if ethical_claims and wage_answer and not wage_confirmed:
        assessment.flags.append(GreenwashingFlag(
            question_id="O-3.3",
            claim="Fair wage / artisan welfare claims",
            flag_message="Brand cannot confirm minimum wage compliance but makes ethical/fair trade claims.",
            priority=FlagPriority.CRITICAL,
            status=ClaimStatus.CONTRADICTED
        ))
        assessment.claim_statuses["fair_wage"] = ClaimStatus.CONTRADICTED

    # ── 3. Organic claim vs. certification ───────────────────────────────────
    if "organic" in claims_text:
        organic_cert = _get(session, "O-2.6")
        if "yes" not in organic_cert and not any(x in organic_cert for x in
                                                  ["gots", "npop", "nop", "organic cert"]):
            assessment.flags.append(GreenwashingFlag(
                question_id="O-2.6",
                claim='"organic" marketing claim',
                flag_message="Brand claims organic materials but cannot name an organic farm or processing certificate.",
                priority=FlagPriority.MODERATE,
                status=ClaimStatus.UNSUBSTANTIATED
            ))
            assessment.claim_statuses["organic"] = ClaimStatus.UNSUBSTANTIATED
        else:
            assessment.claim_statuses["organic"] = ClaimStatus.SUBSTANTIATED

    # ── 4. Recycled claim ────────────────────────────────────────────────────
    if "recycled" in claims_text:
        recycled = _get(session, "O-2.3")
        recycled_confirmed = any(x in recycled for x in ["yes", "recycled", "grs", "rcs", "%"])
        if not recycled_confirmed:
            assessment.flags.append(GreenwashingFlag(
                question_id="O-2.3",
                claim='"recycled" marketing claim',
                flag_message="Brand claims recycled content but reports no recycled materials in O-2.3.",
                priority=FlagPriority.MODERATE,
                status=ClaimStatus.CONTRADICTED
            ))
            assessment.claim_statuses["recycled"] = ClaimStatus.CONTRADICTED
        else:
            assessment.claim_statuses["recycled"] = ClaimStatus.SUBSTANTIATED

    # ── 5. Traceability / transparency claims ────────────────────────────────
    trace_claimed = any(x in claims_text for x in ["traceable", "transparent", "tracibility", "fully traceable"])
    if trace_claimed:
        trace_answer = _get(session, "O-2.7")
        if "no" in trace_answer or "partially" in trace_answer:
            assessment.flags.append(GreenwashingFlag(
                question_id="O-2.7",
                claim="Traceability / transparency claim",
                flag_message="Brand claims traceability but cannot confirm country of material origin.",
                priority=FlagPriority.MODERATE,
                status=ClaimStatus.PARTIALLY_SUBSTANTIATED if "partially" in trace_answer else ClaimStatus.UNSUBSTANTIATED
            ))

    # ── 6. Transparency claims vs. disclosure ────────────────────────────────
    transparency_claim = any(x in claims_text for x in ["transparent", "transparency", "open"])
    if transparency_claim:
        disclosure = _get(session, "O-1.5")
        if "no" in disclosure:
            assessment.flags.append(GreenwashingFlag(
                question_id="O-1.5",
                claim="Transparency claim",
                flag_message="Brand claims transparency but discloses neither supplier list nor pricing breakdown.",
                priority=FlagPriority.MODERATE,
                status=ClaimStatus.UNSUBSTANTIATED
            ))

    # ── 7. Artisan welfare claims vs. pricing data ───────────────────────────
    artisan_claim = any(x in claims_text for x in ["artisan", "fairly paid", "maker", "producer"])
    if artisan_claim:
        pricing = _get(session, "O-4.1")
        if not pricing or "decline" in pricing or "prefer not" in pricing:
            assessment.flags.append(GreenwashingFlag(
                question_id="O-4.1",
                claim="Artisan welfare / fair pay claim",
                flag_message="Brand makes artisan welfare claims but provides no cost breakdown (O-4.1).",
                priority=FlagPriority.MODERATE,
                status=ClaimStatus.UNSUBSTANTIATED
            ))

    # ── 8. Mission vs. claims mismatch ───────────────────────────────────────
    mission = _get(session, "O-1.1")
    if claims_text and not any(x in mission for x in
                               ["sustain", "social", "environment", "impact",
                                "ethical", "artisan", "fair", "organic"]):
        assessment.flags.append(GreenwashingFlag(
            question_id="O-1.1",
            claim="Mission alignment",
            flag_message="Brand makes sustainability claims in marketing but company mission contains no social or environmental reference.",
            priority=FlagPriority.LOW,
            status=ClaimStatus.PARTIALLY_SUBSTANTIATED
        ))

    # ── 9. Handmade / handcrafted claim ─────────────────────────────────────
    if any(x in claims_text for x in ["handmade", "handcrafted", "hand-made", "artisan made"]):
        handcraft = _get(session, "O-2.10") + _get(session, "O-2.9")
        if "no" in handcraft or not handcraft:
            assessment.flags.append(GreenwashingFlag(
                question_id="O-2.10",
                claim='"handmade" / "handcrafted" claim',
                flag_message="Brand claims handmade/handcrafted products but has not confirmed any handcraft techniques.",
                priority=FlagPriority.MODERATE,
                status=ClaimStatus.UNSUBSTANTIATED
            ))
        else:
            assessment.claim_statuses["handmade"] = ClaimStatus.SUBSTANTIATED

    # ── Compute overall risk ──────────────────────────────────────────────────
    assessment.compute_overall_risk()

    # Analyst notes summary
    critical = [f for f in assessment.flags if f.priority == FlagPriority.CRITICAL]
    moderate = [f for f in assessment.flags if f.priority == FlagPriority.MODERATE]
    low      = [f for f in assessment.flags if f.priority == FlagPriority.LOW]

    if not assessment.flags:
        assessment.analyst_notes = (
            "No greenwashing flags raised. All claims appear consistent with Stage 1 evidence. "
            "Recommend standard analyst review before brand goes live."
        )
    else:
        parts = []
        if critical:
            parts.append(f"{len(critical)} critical flag(s) require immediate analyst review before platform access.")
        if moderate:
            parts.append(f"{len(moderate)} moderate flag(s) require follow-up before Stage 2.")
        if low:
            parts.append(f"{len(low)} low-priority flag(s) to be addressed in Stage 2.")
        assessment.analyst_notes = " ".join(parts)

    return assessment


def check_answer_for_flags(
    session: Session,
    question_id: str,
    answer: str
) -> list[GreenwashingFlag]:
    """
    Real-time flag check after a single answer is recorded.
    Returns any new flags triggered by this answer.
    Used during the conversation to catch issues immediately.
    """
    new_flags: list[GreenwashingFlag] = []
    claims = _claims(session)

    if question_id == "O-3.4":
        a = answer.lower()
        labour_confirmed = any(x in a for x in
                               ["yes", "confirmed", "certif", "audit", "no child", "no forced"])
        if not labour_confirmed:
            new_flags.append(GreenwashingFlag(
                question_id="O-3.4",
                claim="Child / forced labour confirmation",
                flag_message="Cannot confirm absence of child or forced labour — highest-priority flag.",
                priority=FlagPriority.CRITICAL,
                status=ClaimStatus.UNSUBSTANTIATED
            ))

    if question_id == "O-2.6" and "organic" in claims:
        a = answer.lower()
        if "no" in a or "unsure" in a:
            new_flags.append(GreenwashingFlag(
                question_id="O-2.6",
                claim='"organic" claim',
                flag_message="Organic claim cannot be substantiated — no organic farm or processing certificate named.",
                priority=FlagPriority.MODERATE,
                status=ClaimStatus.UNSUBSTANTIATED
            ))

    if question_id == "O-2.3" and "recycled" in claims:
        a = answer.lower()
        recycled_confirmed = any(x in a for x in ["yes", "recycled", "grs", "rcs", "%"])
        if not recycled_confirmed:
            new_flags.append(GreenwashingFlag(
                question_id="O-2.3",
                claim='"recycled" claim',
                flag_message="Recycled claim contradicted — brand reports no recycled material use.",
                priority=FlagPriority.MODERATE,
                status=ClaimStatus.CONTRADICTED
            ))

    return new_flags
