"""
Purpose-linkage demo: run 3 illustrative brand sessions through the
Re:Nova verification engine (framework_matcher + greenwashing) and
render the outputs as tables.

This is meant to be dropped into the R Markdown / Jupyter / Quarto
report as-is (a Python code chunk), right next to the limitation
paragraph on keyword matching vs. real RAG.
"""
from src.models import Session
from src.framework_matcher import match_frameworks
from src.greenwashing import run_greenwashing_check
import pandas as pd

pd.set_option("display.max_colwidth", 100)


def build_session(answers: dict) -> Session:
    s = Session()
    for qid, ans in answers.items():
        s.record_answer(qid, ans)
    return s


# ── Example 1: "Clean" brand — claims match evidence ─────────────────────────
clean_brand = build_session({
    "O-1.1": "Our mission is sustainable, ethical fashion with social and environmental impact at its core.",
    "O-1.3": "We are pursuing B Corp certification.",
    "O-1.4": "organic, fair trade, artisan, transparent",
    "O-1.5": "Yes, we publish our supplier list and full pricing breakdown.",
    "O-2.1": "organic cotton, silk",
    "O-2.2": "100% natural fibres",
    "O-2.3": "No recycled materials used.",
    "O-2.4": "No",
    "O-2.6": "Yes, GOTS certified.",
    "O-2.7": "Yes, fully traceable, country and facility of origin confirmed.",
    "O-2.8": "No synthetic dyes, natural dyeing only.",
    "O-2.9": "No",
    "O-2.10": "Yes, hand-embroidered by artisans.",
    "O-2.11": "India, sells to Switzerland and Germany.",
    "O-3.1": "1 cooperative",
    "O-3.2": "Yes, we work with a women's artisan cooperative.",
    "O-3.3": "Yes, confirmed above minimum wage, third-party audited.",
    "O-3.4": "Yes, confirmed via annual audit, no child or forced labour.",
    "O-4.1": "Full cost breakdown provided: materials 40%, labour 30%, overhead 30%.",
})

# ── Example 2: "Red-flag" brand — claims contradicted by evidence ────────────
red_flag_brand = build_session({
    "O-1.1": "We sell affordable, trendy clothing for every season.",
    "O-1.3": "",
    "O-1.4": "organic, ethical, fair trade, artisan, transparent, handmade",
    "O-1.5": "No, we do not share supplier details.",
    "O-2.1": "cotton blend",
    "O-2.2": "roughly 50% cotton",
    "O-2.3": "No recycled content.",
    "O-2.4": "No",
    "O-2.6": "No certificate, we are unsure of organic status.",
    "O-2.7": "No, we don't track country of origin.",
    "O-2.8": "Synthetic dyes used across most lines.",
    "O-2.9": "No",
    "O-2.10": "No",
    "O-2.11": "Factories in Bangladesh, sells worldwide.",
    "O-3.1": "5 factories",
    "O-3.2": "No",
    "O-3.3": "We cannot confirm current wage levels at all facilities.",
    "O-3.4": "We are unsure and cannot confirm absence of child or forced labour.",
    "O-4.1": "",
})

# ── Example 3: "Amber" brand — one substantiated claim, two shaky ones ───────
amber_brand = build_session({
    "O-1.1": "Our mission is to make quality, timeless pieces with environmental awareness in mind.",
    "O-1.3": "",
    "O-1.4": "recycled, traceable",
    "O-1.5": "Yes, we share some supply chain information.",
    "O-2.1": "primarily polyester, small cotton trim",
    "O-2.2": "mostly synthetic, small natural share",
    "O-2.3": "We are still evaluating suppliers; no such materials used yet.",
    "O-2.4": "No",
    "O-2.6": "",
    "O-2.7": "Partially — we know the country but not the specific facility.",
    "O-2.8": "Some synthetic dyes used.",
    "O-2.9": "No",
    "O-2.10": "No",
    "O-2.11": "Vietnam factory, sells to UK and US.",
    "O-3.1": "3 factories",
    "O-3.2": "No",
    "O-3.3": "",
    "O-3.4": "Yes, confirmed via third-party audit, no child or forced labour.",
    "O-4.1": "",
})

EXAMPLES = [
    ("Clean brand", clean_brand),
    ("Red-flag brand", red_flag_brand),
    ("Amber brand", amber_brand),
]


def relevance_table(session: Session, top_n: int = 6) -> pd.DataFrame:
    result = match_frameworks(session)
    rows = [
        {"Rank": e.priority_rank, "Framework": e.acronym, "Reason": e.reason}
        for e in result.relevant_frameworks[:top_n]
    ]
    return pd.DataFrame(rows)


def risk_table(session: Session) -> tuple[str, pd.DataFrame]:
    assessment = run_greenwashing_check(session)
    rows = [
        {
            "Priority": f.priority.value.upper(),
            "Claim": f.claim,
            "Flag": f.flag_message,
            "Status": f.status.value,
        }
        for f in assessment.flags
    ]
    return assessment.overall_risk.value.upper(), pd.DataFrame(rows)


for label, session in EXAMPLES:
    print("=" * 90)
    print(label)
    print("=" * 90)

    print("\n-- Certification Relevance Map (top matches, brand-facing) --")
    rt = relevance_table(session)
    print(rt.to_string(index=False) if not rt.empty else "(none)")

    overall, ft = risk_table(session)
    print(f"\n-- Greenwashing Risk Assessment: OVERALL = {overall} (internal) --")
    print(ft.to_string(index=False) if not ft.empty else "(no flags raised)")
    print()
