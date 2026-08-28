"""
Re:Nova — Claude tool definitions for the Stage 1 intake agent.
"""

RECORD_ANSWER_TOOL = {
    "name": "record_answer",
    "description": (
        "Silently save a brand's answer to a specific Stage 1 question. "
        "Call this after every question response, extracting the key structured data. "
        "The brand does not see this — it runs in the background."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "question_id": {
                "type": "string",
                "description": "The Re:Nova question ID, e.g. O-1.1, O-2.6, O-3.4"
            },
            "raw_answer": {
                "type": "string",
                "description": "The brand's answer, verbatim or closely paraphrased"
            },
            "structured": {
                "type": "object",
                "description": "Key structured fields extracted from the answer",
                "properties": {
                    # O-1.1
                    "mission_text":          {"type": "string"},
                    "has_env_social_mission": {"type": "boolean"},
                    # O-1.2
                    "certifications_held":   {"type": "array", "items": {"type": "string"}},
                    # O-1.3
                    "certifications_pursuing": {"type": "array", "items": {"type": "string"}},
                    # O-1.4
                    "marketing_claims":      {"type": "array", "items": {"type": "string"}},
                    # O-1.5
                    "discloses_suppliers":   {"type": "string", "enum": ["yes", "partial", "no"]},
                    "discloses_pricing":     {"type": "string", "enum": ["yes", "partial", "no"]},
                    # O-2.1
                    "materials":             {"type": "array", "items": {"type": "string"}},
                    # O-2.2
                    "natural_fibre_pct":     {"type": "string"},
                    # O-2.3
                    "has_recycled_content":  {"type": "boolean"},
                    "recycled_details":      {"type": "string"},
                    # O-2.4
                    "has_leather":           {"type": "boolean"},
                    # O-2.5
                    "has_animal_materials":  {"type": "boolean"},
                    "mulesing_free_confirmed": {"type": "boolean"},
                    # O-2.6
                    "organic_certified":     {"type": "boolean"},
                    "organic_cert_name":     {"type": "string"},
                    # O-2.7
                    "material_traceability": {"type": "string", "enum": ["yes", "partially", "no"]},
                    # O-2.8
                    "uses_natural_dyes":     {"type": "string", "enum": ["yes", "no", "partially"]},
                    # O-2.9
                    "uses_handloom":         {"type": "boolean"},
                    "handloom_techniques":   {"type": "array", "items": {"type": "string"}},
                    # O-2.10
                    "uses_handcraft":        {"type": "boolean"},
                    "handcraft_techniques":  {"type": "array", "items": {"type": "string"}},
                    # O-2.11
                    "production_regions":    {"type": "array", "items": {"type": "string"}},
                    # O-3.1
                    "supplier_count_range":  {"type": "string"},
                    # O-3.2
                    "works_with_cooperatives": {"type": "boolean"},
                    "cooperative_names":     {"type": "array", "items": {"type": "string"}},
                    # O-3.3
                    "minimum_wage_confirmed": {"type": "string", "enum": ["yes", "no", "unsure"]},
                    # O-3.4
                    "no_child_forced_labour": {"type": "string", "enum": ["yes", "no", "unsure"]},
                    "labour_evidence_type":  {"type": "string"},
                    # O-4.1
                    "artisan_share_pct":     {"type": "number"},
                    "cost_breakdown_provided": {"type": "boolean"},
                    # O-4.2
                    "payment_terms":         {"type": "string"},
                    "advance_payment":       {"type": "boolean"},
                    # Brand identity (extracted from early conversation)
                    "brand_name":            {"type": "string"},
                }
            }
        },
        "required": ["question_id", "raw_answer"]
    }
}

FLAG_GREENWASHING_TOOL = {
    "name": "flag_greenwashing",
    "description": (
        "Silently raise an internal greenwashing flag when you detect an inconsistency "
        "between a brand's public claims and the evidence they've provided. "
        "This is never shown to the brand — it is an internal analyst note. "
        "Use this only when there is a clear contradiction or unsubstantiated claim."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "question_id":  {"type": "string", "description": "The question that triggered the flag"},
            "claim":        {"type": "string", "description": "The specific claim being flagged"},
            "flag_message": {"type": "string", "description": "Description of the inconsistency"},
            "priority": {
                "type": "string",
                "enum": ["critical", "moderate", "low"],
                "description": "critical = blocks platform access; moderate = follow-up needed; low = Stage 2 item"
            }
        },
        "required": ["question_id", "claim", "flag_message", "priority"]
    }
}

COMPLETE_STAGE1_TOOL = {
    "name": "complete_stage1",
    "description": (
        "Signal that all 21 Stage 1 questions have been covered. "
        "Call this when all 22 Stage 1 questions have been covered. The system will then "
        "generate the Certification Relevance Map and Greenwashing Risk Assessment automatically. "
        "Provide a warm, honest 3–4 sentence closing summary for the brand."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "closing_message": {
                "type": "string",
                "description": (
                    "Warm closing message for the brand: thank them, summarise the key "
                    "things you've learned, and explain what comes next "
                    "(Certification Relevance Map + Stage 2 option)."
                )
            },
            "strengths_observed": {
                "type": "array",
                "items": {"type": "string"},
                "description": "2–3 genuine sustainability strengths you observed during the intake"
            },
            "areas_to_prepare": {
                "type": "array",
                "items": {"type": "string"},
                "description": "1–2 areas where the brand should gather evidence before Stage 2"
            }
        },
        "required": ["closing_message"]
    }
}

ALL_TOOLS = [RECORD_ANSWER_TOOL, FLAG_GREENWASHING_TOOL, COMPLETE_STAGE1_TOOL]
