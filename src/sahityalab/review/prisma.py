"""PRISMA 2020 flow counts and checklist helper.

Counts are supplied by the review team; this module never infers completed
screening stages from imported records.
"""
from __future__ import annotations

from typing import Any

PRISMA_CHECKLIST = [
    (1, "Title", "Identify the report as a systematic review."),
    (2, "Abstract", "Use the PRISMA 2020 for Abstracts checklist."),
    (3, "Rationale", "Describe the rationale in the context of existing knowledge."),
    (4, "Objectives", "Provide an explicit statement of the review objective(s) or question(s)."),
    (5, "Eligibility criteria", "Specify inclusion and exclusion criteria and synthesis groupings."),
    (6, "Information sources", "Specify all databases, registers, websites and other sources searched."),
    (7, "Search strategy", "Present the full search strategies for all databases and sources."),
    (8, "Selection process", "Specify the methods used to decide whether a study met the inclusion criteria."),
    (9, "Data collection process", "Specify the methods used to collect data from reports."),
    (10, "Data items", "List and define all outcomes and other variables sought."),
    (11, "Study risk of bias assessment", "Specify the methods used to assess risk of bias."),
    (12, "Effect measures", "Specify the effect measure(s) used in the synthesis."),
    (13, "Synthesis methods", "Describe the processes used to decide which studies were eligible for each synthesis."),
    (14, "Reporting bias assessment", "Describe methods used to assess risk of bias due to missing results."),
    (15, "Certainty assessment", "Describe methods used to assess certainty or confidence in the body of evidence."),
    (16, "Study selection", "Describe search and selection results, ideally with a flow diagram."),
    (17, "Study characteristics", "Cite each included study and present its characteristics."),
    (18, "Risk of bias in studies", "Present assessments of risk of bias for each included study."),
    (19, "Results of individual studies", "Present results for all outcomes for each study."),
    (20, "Results of syntheses", "Summarise results of all statistical or other syntheses."),
    (21, "Reporting biases", "Present assessments of risk of bias due to missing results."),
    (22, "Certainty of evidence", "Present assessments of certainty or confidence in the body of evidence."),
    (23, "Discussion", "Provide a general interpretation, limitations and implications."),
    (24, "Registration and protocol", "Provide registration information and where the protocol can be accessed."),
    (25, "Support", "Describe sources of financial or non-financial support."),
    (26, "Competing interests", "Declare competing interests."),
    (27, "Availability of data, code and other materials", "Report what is publicly available and where."),
]


def prisma_flow(counts: dict[str, int]) -> dict[str, Any]:
    required = ["identified", "duplicates_removed", "screened", "records_excluded", "full_text_sought", "full_text_not_retrieved", "full_text_assessed", "full_text_excluded", "included"]
    normalized = {key: int(counts.get(key, 0)) for key in required}
    if any(value < 0 for value in normalized.values()):
        raise ValueError("PRISMA counts cannot be negative.")
    checks = {
        "screened_equals_identified_less_duplicates": normalized["screened"] == normalized["identified"] - normalized["duplicates_removed"],
        "full_text_sought_equals_screened_less_excluded": normalized["full_text_sought"] == normalized["screened"] - normalized["records_excluded"],
        "full_text_assessed_equals_sought_less_not_retrieved": normalized["full_text_assessed"] == normalized["full_text_sought"] - normalized["full_text_not_retrieved"],
        "included_equals_assessed_less_full_text_excluded": normalized["included"] == normalized["full_text_assessed"] - normalized["full_text_excluded"],
    }
    return {"counts": normalized, "checks": checks, "internally_consistent": all(checks.values()), "checklist": [{"item": n, "section": s, "requirement": t, "reported_location": "", "status": "not_checked"} for n, s, t in PRISMA_CHECKLIST]}
