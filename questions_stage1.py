"""
Re:Nova — Stage 1 Onboarding Questionnaire.
21 questions across 4 pillars, exactly as defined in the Re:Nova methodology.

Each question carries:
  - id          : canonical question code (O-1.1 etc.)
  - pillar      : Pillar name
  - text        : The question text shown to the brand
  - format      : Expected answer type
  - guidance    : Guidance note for the brand
  - frameworks  : Which of the 26 frameworks this question feeds
  - flag_rule   : Optional greenwashing flag logic (condition + message)
"""
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class FlagRule:
    condition_description: str   # plain-English description of when to flag
    flag_message: str            # what the flag says
    priority: str                # "critical" / "moderate" / "low"

@dataclass
class Stage1Question:
    id: str
    pillar: str
    text: str
    format: str
    guidance: str
    frameworks: list[str]
    flag_rule: Optional[FlagRule] = None
    follow_up_if_yes: Optional[str] = None   # extra probe if answer is affirmative

# ── Pillar 1: Company ─────────────────────────────────────────────────────────

Q_O_1_1 = Stage1Question(
    id="O-1.1",
    pillar="Company",
    text="What is your company's core mission? Does it explicitly reference social or environmental purpose?",
    format="Open text",
    guidance="A few sentences is sufficient. We are not looking for polished language — we want to understand what drives the company.",
    frameworks=["B Corp", "WFTO", "CSRD"],
    flag_rule=FlagRule(
        condition_description="Brand makes sustainability claims in O-1.4 but mission contains no social or environmental reference",
        flag_message="Mission statement contains no social/environmental reference despite public sustainability claims.",
        priority="low"
    )
)

Q_O_1_2 = Stage1Question(
    id="O-1.2",
    pillar="Company",
    text="Do you currently hold any third-party sustainability certification or label? If yes, please list them.",
    format="Yes / No + list",
    guidance="Include any certification at any level: product, supply chain, company-wide, or craft-specific (e.g. Handloom Mark, Craftmark, GOTS, Fair Trade, B Corp, SA8000).",
    frameworks=["All frameworks"],
)

Q_O_1_3 = Stage1Question(
    id="O-1.3",
    pillar="Company",
    text="Are you currently pursuing any certification? If yes, which one and at what stage?",
    format="Yes / No + details",
    guidance="This helps us understand your certification trajectory and prioritise which readiness analysis is most useful to you.",
    frameworks=["All frameworks"],
)

Q_O_1_4 = Stage1Question(
    id="O-1.4",
    pillar="Company",
    text="What sustainability claims do you currently make in your marketing, on your website, or on product labels?",
    format="Open text — list all claims",
    guidance='Examples: "organic cotton", "Fair Trade", "handmade", "zero waste", "carbon neutral", "sustainable". Please list every claim you make, however small.',
    frameworks=["Green Claims Directive", "Fashion Revolution", "CSRD"],
    flag_rule=FlagRule(
        condition_description="Core greenwashing check — each claim cross-referenced against certifications, organic status, traceability, and labour answers",
        flag_message="One or more public claims cannot be substantiated by the information provided in this assessment.",
        priority="moderate"
    )
)

Q_O_1_5 = Stage1Question(
    id="O-1.5",
    pillar="Company",
    text="Do you publicly disclose your supplier list? And do you disclose what proportion of your retail price reaches the artisan or producer?",
    format="Yes / Partial / No — answer each separately",
    guidance="Neither disclosure is currently required by law for brands of this size. Both are voluntary and signal a high level of transparency.",
    frameworks=["Fashion Revolution", "WFTO", "B Corp"],
    flag_rule=FlagRule(
        condition_description="Brand makes 'transparency' or 'ethical' claims in O-1.4 but answers No to both disclosures",
        flag_message="Brand claims transparency/ethical positioning but discloses neither supplier list nor pricing breakdown.",
        priority="moderate"
    )
)

# ── Pillar 2: Product & Materials ─────────────────────────────────────────────

Q_O_2_1 = Stage1Question(
    id="O-2.1",
    pillar="Product & Materials",
    text="Please list all primary materials and fibres used in your products. For each, what is the approximate percentage of total material use?",
    format="Open text — list by fibre with % share",
    guidance="Include everything: cotton, silk, linen, wool, polyester, recycled polyester, leather, viscose, modal, jute, bamboo, etc. For blended products, list all components.",
    frameworks=["GOTS", "GRS", "Oeko-Tex 100", "LWG", "India Organic/NPOP"],
)

Q_O_2_2 = Stage1Question(
    id="O-2.2",
    pillar="Product & Materials",
    text="What percentage of your total material use comes from natural fibres — cotton, silk, linen, wool, jute?",
    format="Select one: 100% / 75–99% / 50–74% / Under 50% / Unsure",
    guidance="Natural fibres are the key eligibility criterion for several certifications including GOTS.",
    frameworks=["GOTS", "Oeko-Tex 100"],
)

Q_O_2_3 = Stage1Question(
    id="O-2.3",
    pillar="Product & Materials",
    text="Do any of your products contain recycled content? If yes, what material and approximately what percentage?",
    format="Yes / No + details",
    guidance="Recycled polyester (rPET), recycled cotton, recycled wool, regenerated fibres. Approximate percentage is sufficient.",
    frameworks=["GRS"],
    flag_rule=FlagRule(
        condition_description="'recycled' claim in O-1.4 but answer here is No or Unsure",
        flag_message="Brand claims recycled content in marketing but reports no recycled materials.",
        priority="moderate"
    )
)

Q_O_2_4 = Stage1Question(
    id="O-2.4",
    pillar="Product & Materials",
    text="Do any of your products contain leather — including leather accessories, trims, or components?",
    format="Yes / No",
    guidance="Including leather accessories, trims, or components.",
    frameworks=["LWG"],
)

Q_O_2_5 = Stage1Question(
    id="O-2.5",
    pillar="Product & Materials",
    text="Do any of your products use animal-derived materials — wool, silk, down, or leather? If yes, for wool specifically: can you confirm your supply chain is free from mulesed sheep?",
    format="Yes / No / N/A + mulesing question separately",
    guidance="Mulesing is the removal of skin from merino sheep without anaesthetic. It is prohibited under GOTS. Non-merino wool breeds are not affected. If you are unsure of your wool's origin or breed, please state this.",
    frameworks=["GOTS", "LWG", "B Corp"],
    flag_rule=FlagRule(
        condition_description="Wool sourced from Australia and mulesing-free status cannot be confirmed",
        flag_message="Potential mulesing risk — wool origin requires clarification before GOTS assessment.",
        priority="low"
    )
)

Q_O_2_6 = Stage1Question(
    id="O-2.6",
    pillar="Product & Materials",
    text="Do you source certified organic fibres? If yes, which certification covers the farms or the processing?",
    format="Yes / No + certification name",
    guidance="Farm-level organic certification (e.g. NPOP, NOP, EU Organic) is separate from processing certification (e.g. GOTS). If you source organic cotton but do not know the farm certification, please state this.",
    frameworks=["GOTS", "India Organic/NPOP"],
    flag_rule=FlagRule(
        condition_description="'organic' claim in O-1.4 but no farm or processing certification named",
        flag_message="Brand claims organic materials but cannot name an organic farm or processing certificate.",
        priority="moderate"
    )
)

Q_O_2_7 = Stage1Question(
    id="O-2.7",
    pillar="Product & Materials",
    text="Can you trace each material back to its country of origin — where the fibre was grown or the recycled material was collected?",
    format="Yes / Partially / No",
    guidance="Country of origin means where the raw material originates — not where the fabric was woven or the garment assembled.",
    frameworks=["GOTS", "ESPR/DPP", "CSDDD", "India Organic/NPOP"],
    flag_rule=FlagRule(
        condition_description="Traceability claims in O-1.4 but answer is No or Partially",
        flag_message="Brand claims traceability but cannot confirm country of material origin.",
        priority="moderate"
    )
)

Q_O_2_8 = Stage1Question(
    id="O-2.8",
    pillar="Product & Materials",
    text="Do you use natural or botanical dyes? If yes, please describe the process briefly.",
    format="Yes / No / Partially",
    guidance="Natural dyes include plant-based (indigo, turmeric, madder), mineral-based, and fermentation-based processes. If you use a mix of natural and synthetic, state approximate proportions.",
    frameworks=["GOTS", "Oeko-Tex 100", "ZDHC"],
)

Q_O_2_9 = Stage1Question(
    id="O-2.9",
    pillar="Product & Materials",
    text="Are any of your products made using handloom weaving? If yes, which techniques — for example Jamdani, Ikat, Banarasi, or Chanderi?",
    format="Yes / No + technique names",
    guidance="Handloom weaving is a key criterion for the Handloom Mark and related Indian craft certifications.",
    frameworks=["Handloom Mark", "Craftmark"],
)

Q_O_2_10 = Stage1Question(
    id="O-2.10",
    pillar="Product & Materials",
    text="Are any products made using traditional handcraft techniques beyond weaving — such as block printing, embroidery, hand-knitting, natural dyeing, or hand-spinning?",
    format="Yes / No + technique names",
    guidance="These techniques are the basis for Craftmark, Nest, and WFTO craft-related certifications.",
    frameworks=["Craftmark", "Nest", "WFTO"],
)

Q_O_2_11 = Stage1Question(
    id="O-2.11",
    pillar="Product & Materials",
    text="What is the country and specific region of manufacture for each main product category?",
    format="Open text — product type + region",
    guidance='For example: "Block-printed kurtas — Bagru, Rajasthan. Handloom silk — Varanasi, Uttar Pradesh." State as specifically as possible — district level is ideal.',
    frameworks=["GOTS", "WFTO", "Sedex/SMETA"],
)

# ── Pillar 3: Supply Chain ────────────────────────────────────────────────────

Q_O_3_1 = Stage1Question(
    id="O-3.1",
    pillar="Supply Chain",
    text="How many production suppliers do you work with in total — meaning the manufacturers or artisan groups you place orders with directly?",
    format="Select one: 1 / 2–5 / 6–15 / 16–50 / More than 50",
    guidance="These are your Tier 1 suppliers — the ones you have a direct commercial relationship with.",
    frameworks=["Sedex/SMETA", "SA8000", "GOTS", "CSDDD"],
)

Q_O_3_2 = Stage1Question(
    id="O-3.2",
    pillar="Supply Chain",
    text="Do you work with artisan cooperatives, self-help groups, NGO-affiliated producer groups, or Fair Trade-certified producers?",
    format="Yes / No + brief description",
    guidance="If yes, please name the group(s) and describe the relationship briefly.",
    frameworks=["WFTO", "Fair Trade", "Nest", "B Corp"],
    follow_up_if_yes="Can you tell me more about those relationships — how long have you worked with them, and are they formally organised as a cooperative or collective?"
)

Q_O_3_3 = Stage1Question(
    id="O-3.3",
    pillar="Supply Chain",
    text="To the best of your knowledge, do all workers in your supply chain receive at least the legal minimum wage in their country?",
    format="Yes / No / Unsure",
    guidance="If you work with cooperatives or home-based workers, include them. If you are unsure, state this honestly — it is more useful than an assumed yes.",
    frameworks=["SA8000", "WFTO", "Fair Trade", "CSDDD"],
    flag_rule=FlagRule(
        condition_description="Answer is No or Unsure AND brand makes ethical, Fair Trade, or artisan welfare claims in O-1.4",
        flag_message="Cannot confirm minimum wage compliance despite making ethical/fair trade claims.",
        priority="critical"
    )
)

Q_O_3_4 = Stage1Question(
    id="O-3.4",
    pillar="Supply Chain",
    text="Do you have evidence that no child labour or forced labour is used in your supply chain?",
    format="Yes / No / Unsure + describe evidence",
    guidance="Evidence can be a supplier declaration, an audit, a cooperative membership agreement, or direct knowledge from working relationships. Unsure is an acceptable answer — it triggers a flag for follow-up, not an automatic rejection.",
    frameworks=["SA8000", "WFTO", "Sedex/SMETA", "CSDDD", "B Corp"],
    flag_rule=FlagRule(
        condition_description="Answer is No or Unsure",
        flag_message="Cannot confirm absence of child or forced labour — highest-priority flag. Immediate analyst review required before brand goes live.",
        priority="critical"
    )
)

# ── Pillar 4: Financial & Commercial ─────────────────────────────────────────

Q_O_4_1 = Stage1Question(
    id="O-4.1",
    pillar="Financial & Commercial",
    text="What is the artisan or producer's share of your retail price? Can you give an approximate cost breakdown for a representative product?",
    format="Open text — materials / production / logistics / margin as % of retail",
    guidance='This does not need to be precise. Even an approximate breakdown — "roughly 20% goes to the maker, 15% is materials, 10% logistics, 55% is our margin" — is far more informative than no answer. The artisan or producer labour share is the figure that matters most.',
    frameworks=["WFTO", "Fair Trade", "Fashion Revolution", "B Corp"],
    flag_rule=FlagRule(
        condition_description="Brand makes artisan welfare or Fair Trade claims in O-1.4 but declines to provide any pricing information",
        flag_message="Brand claims artisan welfare/fair pricing but provides no cost breakdown.",
        priority="moderate"
    )
)

Q_O_4_2 = Stage1Question(
    id="O-4.2",
    pillar="Financial & Commercial",
    text="What are your standard payment terms with suppliers? Do you pay in advance, on delivery, or on extended credit terms?",
    format="Open text",
    guidance="Standard industry terms are 30–60 days after delivery. Advance payment before production (30–50% of order value) is considered best practice for home-based and cooperative producers who cannot pre-finance materials.",
    frameworks=["WFTO", "Fair Trade", "CSDDD"],
)

# ── Master question list ──────────────────────────────────────────────────────

STAGE1_QUESTIONS: list[Stage1Question] = [
    Q_O_1_1, Q_O_1_2, Q_O_1_3, Q_O_1_4, Q_O_1_5,
    Q_O_2_1, Q_O_2_2, Q_O_2_3, Q_O_2_4, Q_O_2_5,
    Q_O_2_6, Q_O_2_7, Q_O_2_8, Q_O_2_9, Q_O_2_10,
    Q_O_2_11,
    Q_O_3_1, Q_O_3_2, Q_O_3_3, Q_O_3_4,
    Q_O_4_1, Q_O_4_2,
]

QUESTIONS_BY_ID = {q.id: q for q in STAGE1_QUESTIONS}
