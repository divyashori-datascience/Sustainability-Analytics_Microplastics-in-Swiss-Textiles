"""
Re:Nova — Framework Relevance Matcher.

Implements the exact framework relevance filter rules from the Re:Nova
Assessment Methodology document, using Stage 1 answers.

For each of the 26 frameworks: returns RELEVANT or EXCLUDED with a
one-line explanation for the brand-facing Certification Relevance Map.
"""
from __future__ import annotations
from .models import (
    Session, FrameworkEntry, FrameworkRelevance, CertificationRelevanceMap
)


# ── Framework catalogue ────────────────────────────────────────────────────────

FRAMEWORKS = {
    "GOTS": "Global Organic Textile Standard",
    "GRS": "Global Recycled Standard",
    "Fair Trade": "Fair Trade Certification",
    "WFTO": "World Fair Trade Organization",
    "Nest": "Nest Ethical Handcraft Standard",
    "SA8000": "Social Accountability Standard (SA8000)",
    "Sedex/SMETA": "Sedex / SMETA Audit",
    "BSCI": "Business Social Compliance Initiative",
    "Oeko-Tex 100": "Oeko-Tex Standard 100",
    "B Corp": "B Corporation Certification",
    "ZWIA": "Zero Waste International Alliance",
    "ZDHC": "Zero Discharge of Hazardous Chemicals",
    "FSC": "Forest Stewardship Council",
    "LWG": "Leather Working Group",
    "C2C": "Cradle to Cradle",
    "COSMOS": "Ecocert / COSMOS",
    "Leaping Bunny": "Leaping Bunny / PETA Vegan",
    "USDA Organic": "USDA Organic",
    "Non-GMO": "Non-GMO Project Verified",
    "Rainforest Alliance": "Rainforest Alliance",
    "India Organic/NPOP": "India Organic / NPOP",
    "Handloom Mark": "Handloom Mark (India)",
    "Craftmark": "Craftmark (India)",
    "Fashion Revolution": "Fashion Revolution Transparency Index",
    "Green Claims Directive": "EU Green Claims Directive",
    "CSRD": "EU Corporate Sustainability Reporting Directive",
}


def _get(session: Session, qid: str) -> str:
    """Get a raw answer string, lowercased, or empty string."""
    ans = session.answers.get(qid)
    return (ans.raw_answer or "").lower() if ans else ""

def _structured(session: Session, qid: str) -> dict:
    ans = session.answers.get(qid)
    return ans.structured if ans else {}

def _facts(session: Session) -> dict:
    return session.facts


def _has_natural_fibres(session: Session) -> bool:
    a = _get(session, "O-2.2")
    return any(x in a for x in ["100%", "75", "50", "under 50"]) or \
           any(f in _get(session, "O-2.1") for f in
               ["cotton", "silk", "linen", "wool", "jute", "hemp", "bamboo", "modal"])

def _has_wet_processing(session: Session) -> bool:
    a = _get(session, "O-2.8")
    # Also infer from synthetic dyes / no natural dye answer
    return "no" not in a or "partially" in a or \
           any(x in _get(session, "O-2.1") for x in ["dye", "print"])

def _claims_organic(session: Session) -> bool:
    return "organic" in _get(session, "O-1.4")

def _has_recycled(session: Session) -> bool:
    a = _get(session, "O-2.3")
    return "yes" in a or "recycled" in a

def _has_leather(session: Session) -> bool:
    return "yes" in _get(session, "O-2.4")

def _has_handloom(session: Session) -> bool:
    return "yes" in _get(session, "O-2.9")

def _has_handcraft(session: Session) -> bool:
    return "yes" in _get(session, "O-2.10")

def _has_cooperative(session: Session) -> bool:
    return "yes" in _get(session, "O-3.2")

def _supplier_count(session: Session) -> str:
    return _get(session, "O-3.1")

def _sells_to_eu(session: Session) -> bool:
    markets = _get(session, "O-2.11") + _get(session, "O-1.4")
    return any(x in markets for x in ["europe", "eu", "germany", "france", "netherlands",
                                       "italy", "spain", "switzerland", "uk"])

def _makes_claims(session: Session) -> bool:
    a = _get(session, "O-1.4")
    return bool(a) and "none" not in a and "no claim" not in a

def _indian_production(session: Session) -> bool:
    r = _get(session, "O-2.11")
    return "india" in r or "rajasthan" in r or "gujarat" in r or \
           "varanasi" in r or "bengal" in r or "tamil" in r

def _has_organic_cert(session: Session) -> bool:
    a = _get(session, "O-2.6")
    return "yes" in a or any(x in a for x in ["gots", "npop", "nop", "organic"])

def _pursues_b_corp(session: Session) -> bool:
    return "b corp" in _get(session, "O-1.3").lower()

def _has_gov_commitment(session: Session) -> bool:
    mission = _get(session, "O-1.1")
    return any(x in mission for x in ["mission", "purpose", "sustainability",
                                       "social", "environmental", "impact"])


# ── Main matching function ────────────────────────────────────────────────────

def match_frameworks(session: Session, brand_name: str = None) -> CertificationRelevanceMap:
    """
    Evaluate all 26 frameworks against Stage 1 answers.
    Returns a CertificationRelevanceMap with included + excluded entries.
    """
    relevant: list[FrameworkEntry] = []
    excluded: list[FrameworkEntry] = []

    def add_relevant(key: str, reason: str) -> None:
        relevant.append(FrameworkEntry(
            name=FRAMEWORKS[key], acronym=key,
            relevance=FrameworkRelevance.RELEVANT, reason=reason
        ))

    def add_excluded(key: str, reason: str) -> None:
        excluded.append(FrameworkEntry(
            name=FRAMEWORKS[key], acronym=key,
            relevance=FrameworkRelevance.EXCLUDED, reason=reason
        ))

    # ── GOTS ──
    if _has_natural_fibres(session) and (_claims_organic(session) or _has_organic_cert(session)):
        add_relevant("GOTS",
            "You use natural fibres and source or claim organic materials — GOTS is the primary certification for your supply chain.")
    elif _has_natural_fibres(session):
        add_relevant("GOTS",
            "You use natural fibres. GOTS is relevant as a processing-level standard even without current organic farm certification.")
    else:
        add_excluded("GOTS",
            "GOTS requires natural fibres (cotton, silk, linen, wool etc.) — your current material mix does not meet the eligibility threshold.")

    # ── GRS ──
    if _has_recycled(session):
        add_relevant("GRS",
            "You use recycled content — GRS is the primary certification for recycled material claims.")
    else:
        add_excluded("GRS",
            "GRS requires recycled content — not applicable as you have not indicated use of recycled materials.")

    # ── Fair Trade ──
    if _has_cooperative(session):
        add_relevant("Fair Trade",
            "You work with producer cooperatives or artisan groups — Fair Trade certification is directly applicable.")
    else:
        add_excluded("Fair Trade",
            "Fair Trade requires a direct producer relationship with a qualifying group — not applicable given your current supply chain structure.")

    # ── WFTO ──
    if _has_cooperative(session):
        add_relevant("WFTO",
            "WFTO membership is relevant for brands with genuine cooperative or fair trade producer relationships — one of the most comprehensive fair trade certifications available.")
    else:
        add_excluded("WFTO",
            "WFTO is for brands with cooperative or fair trade producer relationships.")

    # ── Nest ──
    if _has_handcraft(session) or _has_cooperative(session):
        add_relevant("Nest",
            "Nest is specifically designed for brands working with home-based artisans and craft workers — directly relevant to your supply chain.")
    else:
        add_excluded("Nest",
            "Nest is for brands working with home-based or informal artisan producers.")

    # ── SA8000 ──
    sc = _supplier_count(session)
    if sc and "1" not in sc[:1]:
        add_relevant("SA8000",
            "SA8000 is a facility-level social standard — relevant for brands with multiple production suppliers.")
    else:
        add_excluded("SA8000",
            "SA8000 is most applicable for brands with multiple manufacturing suppliers — lower priority for single-supplier or direct-artisan models.")

    # ── Sedex/SMETA ──
    if sc and ("2" in sc or "6" in sc or "16" in sc or "more" in sc):
        add_relevant("Sedex/SMETA",
            "Sedex/SMETA is widely required by European retail buyers for supplier social compliance — relevant for your scale of supply chain.")
    else:
        add_excluded("Sedex/SMETA",
            "Lower priority for single-supplier or direct cooperative brands.")

    # ── BSCI ──
    if _sells_to_eu(session) and sc and "1" not in sc[:1]:
        add_relevant("BSCI",
            "BSCI is requested by many European retail buyers — relevant if you are or plan to supply European retailers.")
    else:
        add_excluded("BSCI",
            "BSCI is relevant primarily for brands supplying European retail buyers with multi-tier supply chains.")

    # ── Oeko-Tex 100 ── (always relevant for textile/fashion brands)
    add_relevant("Oeko-Tex 100",
        "Oeko-Tex 100 is the practical baseline certification for all textile brands — tests finished products for harmful substances. Relevant regardless of your current material mix.")

    # ── B Corp ──
    if _pursues_b_corp(session) or _has_gov_commitment(session):
        add_relevant("B Corp",
            "B Corp is the most comprehensive company-wide sustainability certification — relevant given your stated mission and governance commitment.")
    else:
        add_excluded("B Corp",
            "B Corp is relevant for mission-driven brands with governance commitments across all impact areas.")

    # ── ZWIA ──
    if "zero waste" in _get(session, "O-1.4") or "zero waste" in _get(session, "O-1.1"):
        add_relevant("ZWIA",
            "You make zero-waste claims — ZWIA certification provides formal verification for these.")
    else:
        add_excluded("ZWIA",
            "ZWIA is for brands with specific zero-waste production or packaging claims.")

    # ── ZDHC ──
    dye_answer = _get(session, "O-2.8")
    if "no" not in dye_answer or "synthetic" in _get(session, "O-2.1"):
        add_relevant("ZDHC",
            "ZDHC is relevant for any brand using dyes, finishes, or chemical processing — it sets chemical management standards for wet processing.")
    else:
        add_excluded("ZDHC",
            "ZDHC applies to brands using industrial dyes or chemical processing. Natural-dye or dry-craft brands are exempt.")

    # ── FSC ──
    packaging = _get(session, "O-1.4") + _get(session, "O-1.1")
    if "wood" in packaging or "paper" in packaging or "packaging" in packaging or "forest" in packaging:
        add_relevant("FSC",
            "FSC is relevant for brands using paper/wood packaging or wood-derived products.")
    else:
        add_excluded("FSC",
            "FSC covers wood and forest-derived products — not a priority for your current product mix.")

    # ── LWG ──
    if _has_leather(session):
        add_relevant("LWG",
            "LWG is the primary certification for leather tanneries — essential if you use leather in any products.")
    else:
        add_excluded("LWG",
            "LWG applies only to brands using leather — not applicable to your product range.")

    # ── C2C ──
    materials = _get(session, "O-2.1") + _get(session, "O-2.7")
    if "recycl" in materials or "circular" in _get(session, "O-1.1") or "upcycl" in _get(session, "O-1.1"):
        add_relevant("C2C",
            "Cradle to Cradle is relevant for brands with circular design or material recovery programmes.")
    else:
        add_excluded("C2C",
            "C2C is for brands with a circular economy model — not a priority at current stage.")

    # ── COSMOS / Leaping Bunny / USDA Organic / Non-GMO ──
    sector_hints = _get(session, "O-2.1") + _get(session, "O-2.11") + _get(session, "O-1.1")
    if "beauty" in sector_hints or "cosmetic" in sector_hints or "skincare" in sector_hints or "personal care" in sector_hints:
        add_relevant("COSMOS", "COSMOS is the primary organic certification for personal care and beauty products.")
        add_relevant("Leaping Bunny", "Leaping Bunny is relevant for beauty/personal care brands — cruelty-free certification widely recognised by consumers.")
    else:
        add_excluded("COSMOS", "COSMOS is for personal care and beauty product brands.")
        add_excluded("Leaping Bunny", "Leaping Bunny applies to beauty and personal care brands.")

    if "food" in sector_hints or "ingredient" in sector_hints or "agricultural" in sector_hints:
        add_relevant("USDA Organic", "USDA Organic is relevant if you sell food or agricultural ingredients into the US market.")
        add_relevant("Non-GMO", "Non-GMO Project Verified is relevant for food and ingredient brands.")
        add_relevant("Rainforest Alliance", "Rainforest Alliance is relevant for agricultural, food, or natural material brands.")
    else:
        add_excluded("USDA Organic", "USDA Organic applies to food and agricultural ingredient brands selling into the US.")
        add_excluded("Non-GMO", "Non-GMO Project Verified is for food and agricultural ingredient brands.")
        add_excluded("Rainforest Alliance", "Rainforest Alliance covers agricultural and food supply chains.")

    # ── India Organic / NPOP ──
    if _indian_production(session) and (_claims_organic(session) or _has_organic_cert(session)):
        add_relevant("India Organic/NPOP",
            "You produce in India and source or claim organic materials — India Organic/NPOP is the national certification for organic fibres and products.")
    else:
        add_excluded("India Organic/NPOP",
            "India Organic/NPOP is for brands sourcing organic cotton or fibres grown in India.")

    # ── Handloom Mark ──
    if _has_handloom(session):
        add_relevant("Handloom Mark",
            "You use traditional handloom weaving — the Handloom Mark is the Indian government certification for authentic handloom products.")
    else:
        add_excluded("Handloom Mark",
            "The Handloom Mark applies only to products made with traditional handloom weaving techniques.")

    # ── Craftmark ──
    if _has_handcraft(session) or _has_handloom(session):
        add_relevant("Craftmark",
            "You work with traditional handcraft techniques — Craftmark certifies authentic Indian handcrafted products.")
    else:
        add_excluded("Craftmark",
            "Craftmark applies to products made using traditional Indian handcraft techniques.")

    # ── Fashion Revolution ──
    if _makes_claims(session):
        add_relevant("Fashion Revolution",
            "Fashion Revolution's Transparency Index is relevant to any brand making public sustainability claims — it assesses the quality and substance of those claims.")
    else:
        add_excluded("Fashion Revolution",
            "Fashion Revolution is most relevant for brands actively making public sustainability claims.")

    # ── Green Claims Directive ──
    if _makes_claims(session):
        add_relevant("Green Claims Directive",
            "You make sustainability claims in your marketing — the EU Green Claims Directive requires any brand selling into EU markets to substantiate all such claims. Relevant regardless of your current sales geography as future-readiness.")
    else:
        add_excluded("Green Claims Directive",
            "The Green Claims Directive is relevant only if you make public sustainability claims.")

    # ── CSRD ──
    if _sells_to_eu(session):
        add_relevant("CSRD",
            "You sell into EU markets — CSRD sustainability reporting requirements are relevant to your supply chain partners and may become relevant to your own reporting as you scale.")
    else:
        add_excluded("CSRD",
            "CSRD is primarily relevant for brands selling into EU markets or in the supply chains of larger EU companies.")

    # ── Rank the relevant frameworks ──
    # Priority order: certifications most actionable for small artisan brands first
    priority_order = [
        "Oeko-Tex 100", "GOTS", "India Organic/NPOP", "Handloom Mark", "Craftmark",
        "GRS", "Nest", "Fair Trade", "WFTO", "SA8000", "Sedex/SMETA", "BSCI",
        "ZDHC", "B Corp", "Fashion Revolution", "Green Claims Directive",
        "LWG", "FSC", "COSMOS", "Leaping Bunny", "ZWIA", "C2C", "CSRD",
        "USDA Organic", "Non-GMO", "Rainforest Alliance"
    ]
    for i, entry in enumerate(relevant):
        try:
            entry.priority_rank = priority_order.index(entry.acronym) + 1
        except ValueError:
            entry.priority_rank = 99
    relevant.sort(key=lambda e: e.priority_rank or 99)

    # Analyst summary
    relevant_names = [e.acronym for e in relevant[:5]]
    summary = (
        f"Based on your Stage 1 responses, {len(relevant)} of the 26 Re:Nova frameworks "
        f"are relevant to your brand. The highest-priority frameworks for your assessment are: "
        f"{', '.join(relevant_names)}. "
        f"{len(excluded)} frameworks have been excluded as not applicable to your current "
        f"product mix, geography, or supply chain structure."
    )

    return CertificationRelevanceMap(
        session_id=session.id,
        brand_name=brand_name or session.facts.get("brand_name"),
        relevant_frameworks=relevant,
        excluded_frameworks=excluded,
        analyst_summary=summary
    )
