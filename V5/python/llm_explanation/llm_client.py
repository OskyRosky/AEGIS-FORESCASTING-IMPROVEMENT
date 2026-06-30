"""
AEGIS V4 - V4.4 Local Mock Provider (NO real LLM, NO Azure).

This module defines a DETERMINISTIC local mock provider that turns the governed
V4.3 deterministic insights into a controlled executive narrative shaped like the
final panel (summary / evidence / why it matters / sources / limitations / payload).

Honesty guardrails (hard):
  - provider = "mock", provider_stage = "mock_no_llm".
  - This is NOT a real LLM. No network call, no Azure OpenAI, no external API.
  - It invents NO facts. Every sentence is composed from V4.3 card messages,
    risk flags, claims traceability, sources and limitations.
  - Same input -> same output (pure composition, no randomness, no timestamps in body).
"""

from __future__ import annotations

import json
import re

PROVIDER = "mock"
PROVIDER_STAGE = "mock_no_llm"

# --- forbidden language guard (kept self-contained for V4.4) -------------------------
FORBIDDEN_WORDS = ["winner", "best", "promoted", "promote"]
FORBIDDEN_PHRASES = [
    "unconditional champion",
    "promoted champion",
    "production approved",
    "automatic decision",
]
SANITIZE_PHRASES = [
    ("unconditional champion", "governed champion"),
    ("promoted champion", "documented challenger"),
    ("production approved", "review stage"),
    ("automatic decision", "documented decision"),
]
SANITIZE_WORDS = [
    ("best", "leading"),
    ("winner", "leading candidate"),
    ("promoted", "retained"),
    ("promote", "retain"),
]

PAGE_TITLES = {
    "champion_overview": "Champion Overview",
    "tournament": "Tournament",
    "forecast_viewer": "Forecast Viewer",
    "governance_risks": "Governance & Risks",
    "executive_overview": "Executive Overview",
}

# Controlled, reviewer-facing "why it matters" framing per page. No decisions implied.
WHY_IT_MATTERS = {
    "champion_overview": (
        "These figures describe the champion under governed conditions only. They are "
        "presented so reviewers can see the current accuracy of record and the size of "
        "the governed scope. Nothing here advances or changes the champion; the numbers "
        "support human review, not a documented decision."
    ),
    "tournament": (
        "The ranking matters because it makes the recorded distance between the champion "
        "and its documented challengers explicit and reviewable. It is shown so reviewers "
        "can read the comparison directly, without implying any change of standing."
    ),
    "forecast_viewer": (
        "This view matters because the forecast evidence is deliberately filtered, "
        "summarized, and capped before any explanation, and because the model labels here "
        "belong to a different namespace than the tournament names. Showing both protects "
        "reviewers from conflating productive labels with governed model names."
    ),
    "governance_risks": (
        "Governance matters because the explanation is bounded strictly by the recorded "
        "evidence pack. The time-to-live coverage and the count of models carrying a "
        "recorded risk flag are surfaced so reviewers can see the governed footprint "
        "without inferring risks beyond the data."
    ),
    "executive_overview": (
        "This overview matters because it gives reviewers a single governed read across "
        "the champion, the documented challengers, the forecast evidence and the "
        "governance footprint. It is a controlled summary for human review; it does not "
        "advance, change, or decide anything."
    ),
}

CONF_RANK = {"high": 3, "medium": 2, "low": 1}
CONF_NAME = {3: "high", 2: "medium", 1: "low"}


def sanitize_text(text):
    """Return (sanitized_text, changed) neutralizing forbidden language."""
    if not isinstance(text, str) or not text:
        return text, False
    out = text
    for bad, good in SANITIZE_PHRASES:
        out = re.sub(re.escape(bad), good, out, flags=re.IGNORECASE)
    for bad, good in SANITIZE_WORDS:
        out = re.sub(rf"\b{re.escape(bad)}\b", good, out, flags=re.IGNORECASE)
    return out, (out != text)


def scan_forbidden(obj) -> list:
    """Recursively scan any structure for forbidden tokens (word-boundary aware)."""
    hits = []
    blob = json.dumps(obj, ensure_ascii=False).lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase in blob:
            hits.append(phrase)
    for word in FORBIDDEN_WORDS:
        if re.search(rf"\b{re.escape(word)}\b", blob):
            hits.append(word)
    return sorted(set(hits))


def _dedupe(seq):
    seen = set()
    out = []
    for item in seq:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


class MockLLMClient:
    """
    Deterministic local mock provider.

    It accepts a structured `request` (already governed evidence from V4.3) and returns a
    structured narrative response. It performs NO real inference and NO network access.
    """

    provider = PROVIDER
    provider_stage = PROVIDER_STAGE

    @staticmethod
    def is_real_llm() -> bool:
        return False

    @staticmethod
    def uses_azure() -> bool:
        return False

    def generate(self, request: dict) -> dict:
        """
        request keys:
          page_id (str), title (str),
          primary_cards (list of card dicts, display_order < 90),
          governance_cards (list of card dicts, display_order >= 90),
          risk_flags (list), claims (list), insufficient (bool),
          source_files (list of V4.3 filenames used)
        """
        page_id = request["page_id"]
        title = request.get("title") or PAGE_TITLES.get(page_id, page_id)
        primary = request.get("primary_cards", [])
        governance = request.get("governance_cards", [])
        risk_flags = request.get("risk_flags", [])
        claims = request.get("claims", [])
        insufficient = bool(request.get("insufficient", False))
        source_files = request.get("source_files", [])

        if insufficient or not primary:
            return self._insufficient_response(page_id, title, source_files, governance)

        # Evidence bullets straight from governed card messages (no invention).
        evidence_bullets = [c["message"] for c in primary]

        # Executive summary: compose from the first substantive messages.
        lead = primary[0]["message"]
        rest = " ".join(c["message"] for c in primary[1:])
        summary = (
            f"Under governed, evidence-only conditions, {self._lower_first(lead)} "
            f"{rest}".strip()
        )
        summary = re.sub(r"\s+", " ", summary)

        why = WHY_IT_MATTERS.get(page_id, WHY_IT_MATTERS["executive_overview"])

        # Sources = union of card source_artifacts + V4.3 files consumed.
        sources = _dedupe(
            [s for c in (primary + governance) for s in c.get("source_artifacts", [])]
            + source_files
        )

        # Limitations = union of card limitations + risk flags surfaced as limitations.
        limitations = _dedupe(
            [lim for c in (primary + governance) for lim in c.get("limitations", [])]
            + [f"Risk flag: {rf['message']}" for rf in risk_flags]
        )

        # Confidence = lowest confidence across substantive cards.
        confidence = self._aggregate_confidence(primary)

        response = {
            "page_id": page_id,
            "title": title,
            "summary": summary,
            "what_the_evidence_says": evidence_bullets,
            "why_it_matters": why,
            "sources_used": sources,
            "limitations": limitations,
            "confidence": confidence,
            "claims_traceability": claims,
            "download_payload": self._download_payload(page_id, primary + governance, source_files),
        }
        return self._sanitize_response(response)

    def generate_executive(self, page_responses: list, source_files: list) -> dict:
        """Aggregate the per-page narratives into one controlled executive overview."""
        page_id = "executive_overview"
        title = PAGE_TITLES[page_id]

        # Pull the lead substantive bullet from each governed page (no invention).
        evidence_bullets = []
        sources = []
        limitations = []
        claims = []
        confidences = []
        for r in page_responses:
            if r.get("what_the_evidence_says"):
                evidence_bullets.append(
                    f"{PAGE_TITLES.get(r['page_id'], r['page_id'])}: {r['what_the_evidence_says'][0]}"
                )
            sources.extend(r.get("sources_used", []))
            limitations.extend(r.get("limitations", []))
            claims.extend(r.get("claims_traceability", []))
            confidences.append(r.get("confidence", "high"))

        if not evidence_bullets:
            return self._insufficient_response(page_id, title, source_files, [])

        summary = (
            "This is a governed, evidence-only read across the AEGIS V4 layer, produced by a "
            "local deterministic mock provider (no real LLM is active). It draws only on the "
            "V4.3 deterministic insights: the champion under governed conditions, the "
            "documented challengers, the filtered forecast evidence and the governance "
            "footprint. It is a controlled summary for human review and changes nothing."
        )
        confidence = CONF_NAME[min(CONF_RANK.get(c, 3) for c in confidences)] if confidences else "high"

        response = {
            "page_id": page_id,
            "title": title,
            "summary": summary,
            "what_the_evidence_says": _dedupe(evidence_bullets),
            "why_it_matters": WHY_IT_MATTERS[page_id],
            "sources_used": _dedupe(sources + source_files),
            "limitations": _dedupe(limitations),
            "confidence": confidence,
            "claims_traceability": claims,
            "download_payload": self._download_payload(page_id, [], source_files),
        }
        return self._sanitize_response(response)

    # --- internals --------------------------------------------------------------------
    def _insufficient_response(self, page_id, title, source_files, governance):
        limitations = _dedupe(
            [lim for c in governance for lim in c.get("limitations", [])]
            + ["Insufficient evidence: no substantive governed insight cards were available for this page."]
        ) or ["Insufficient evidence for this page."]
        response = {
            "page_id": page_id,
            "title": title,
            "summary": "Insufficient evidence. The governed evidence pack did not contain "
                       "substantive insight cards for this page, so no narrative is produced.",
            "what_the_evidence_says": ["Insufficient evidence."],
            "why_it_matters": "With insufficient evidence, no executive interpretation is offered. "
                              "This protects reviewers from reading meaning into missing data.",
            "sources_used": _dedupe(source_files) or ["v4_3_deterministic_insights.json"],
            "limitations": limitations,
            "confidence": "low",
            "claims_traceability": [],
            "download_payload": self._download_payload(page_id, [], source_files),
        }
        return self._sanitize_response(response)

    @staticmethod
    def _download_payload(page_id, cards, source_files):
        return {
            "page_id": page_id,
            "format_options": ["md", "json"],
            "available_in_phase": "V4.7",
            "card_count": len(cards),
            "source_files": _dedupe(source_files),
            "note": "Download UI is deferred to V4.7; the payload structure is shown here "
                    "for traceability only.",
        }

    @staticmethod
    def _aggregate_confidence(cards):
        ranks = [CONF_RANK.get(str(c.get("confidence", "high")).lower(), 3) for c in cards]
        return CONF_NAME[min(ranks)] if ranks else "high"

    @staticmethod
    def _lower_first(text):
        return text[:1].lower() + text[1:] if text else text

    @staticmethod
    def _sanitize_response(response):
        # Sanitize every user-visible text field; cards came clean from V4.3 but we re-guard.
        for key in ("summary", "why_it_matters"):
            response[key], _ = sanitize_text(response[key])
        response["what_the_evidence_says"] = [sanitize_text(b)[0] for b in response["what_the_evidence_says"]]
        response["limitations"] = [sanitize_text(b)[0] for b in response["limitations"]]
        return response
