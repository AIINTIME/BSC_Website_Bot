"""
FAQ / Knowledge-Base loader for BSC Website Bot.

Handles two JSON shapes:
  1. Flat list  — each item already has id, question, answer fields.
  2. BSC website dict — hierarchical JSON; extracts FAQs from *all* page sections.

BSC extraction covers:
  - pages.membership.faqs          → Membership FAQs
  - pages.facilities.facility_details → Facility descriptions
  - pages.academies.academies_list → Academy program details
  - pages.*.hero / intro sections  → Hero/intro text content
"""
import json
from typing import Any, Dict, List


def load_faqs(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # ── Case 1: Already a flat list ──────────────────────────────────────────
    if isinstance(data, list):
        out = []
        for i, item in enumerate(data, start=1):
            if isinstance(item, dict):
                item.setdefault("id", f"BSC_FAQ_{i}")
                out.append(item)
        return out

    # ── Case 2: BSC hierarchical website JSON ─────────────────────────────────
    if isinstance(data, dict):
        out = []
        pages = data.get("pages", {})

        # 2a) Membership explicit FAQs
        for i, item in enumerate(pages.get("membership", {}).get("faqs", []), start=1):
            if not isinstance(item, dict):
                continue
            out.append({
                "id": f"BSC_MEM_FAQ_{i}",
                "category": "Membership",
                "question": (item.get("question") or "").strip(),
                "answer": (item.get("answer") or "").strip(),
                "keywords": ["membership", "plans", "pricing"],
                "source": "website_json",
            })

        # 2b) Facility details
        for i, fac in enumerate(pages.get("facilities", {}).get("facility_details", []), start=1):
            if not isinstance(fac, dict):
                continue
            features_text = "; ".join(fac.get("features", []))
            answer = (
                f"{fac.get('description', '').strip()} "
                f"Features: {features_text}."
            ).strip()
            if fac.get("operating_hours"):
                answer += f" Operating Hours: {fac['operating_hours']}."
            if fac.get("capacity"):
                answer += f" Capacity: {fac['capacity']}."
            if fac.get("courts"):
                answer += f" Courts: {fac['courts']}."

            out.append({
                "id": f"BSC_FAC_{i}",
                "category": f"Facilities – {fac.get('name', '')}",
                "question": f"What facilities does {fac.get('name', 'this facility')} offer?",
                "answer": answer,
                "keywords": [fac.get("id", ""), fac.get("category", ""), "facility"],
                "source": "website_json",
            })

        # 2c) Academy programs
        for i, ac in enumerate(pages.get("academies", {}).get("academies_list", []), start=1):
            if not isinstance(ac, dict):
                continue
            highlights = "; ".join(ac.get("curriculum_highlights", []))
            age_groups = ", ".join(ac.get("age_groups", []))
            answer = (
                f"{ac.get('description', '').strip()} "
                f"Age Groups: {age_groups}. "
                f"Sessions per week: {ac.get('sessions_per_week', 'N/A')}. "
                f"Monthly Fee: BDT {ac.get('monthly_fee', 'Contact us')}. "
                f"Curriculum: {highlights}."
            ).strip()

            out.append({
                "id": f"BSC_ACAD_{i}",
                "category": f"Academies – {ac.get('name', '')}",
                "question": f"Tell me about the {ac.get('name', 'academy')} program.",
                "answer": answer,
                "keywords": [ac.get("id", ""), "academy", "coaching", "training"],
                "source": "website_json",
            })

        # 2d) Membership plans (detailed)
        for i, plan in enumerate(pages.get("membership", {}).get("plans", []), start=1):
            if not isinstance(plan, dict):
                continue
            features = "; ".join(plan.get("features", []))
            price_info = (
                f"BDT {plan.get('monthly_price', 'Custom')}/month"
                if plan.get("monthly_price")
                else plan.get("note", "Contact us")
            )
            answer = (
                f"{plan.get('description', '').strip()} "
                f"Price: {price_info}. "
                f"Includes: {features}."
            ).strip()

            out.append({
                "id": f"BSC_PLAN_{i}",
                "category": "Membership Plans",
                "question": f"What does the {plan.get('name', '')} membership plan include?",
                "answer": answer,
                "keywords": [plan.get("id", ""), "membership", "plan", "price"],
                "source": "website_json",
            })

        return out

    return []