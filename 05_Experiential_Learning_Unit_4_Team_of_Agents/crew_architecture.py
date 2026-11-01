"""
Research & Report Writing Crew — crew_architecture.py
======================================================
Implements a 3-agent crew with clear separation of responsibilities:

    ResearcherAgent  → finds and summarises information
    WriterAgent      → drafts report sections from research summaries
    EditorAgent      → reviews drafts for clarity and completeness

Each agent receives structured input from the previous agent.
"""

import datetime
import textwrap


# ===========================================================================
# Shared Data Structures
# ===========================================================================

def _ts() -> str:
    return datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"


# Mock search database
_MOCK_SEARCH_DB: dict[str, list[dict]] = {
    "artificial intelligence": [
        {"title": "AI Fundamentals", "summary": "AI enables machines to mimic human intelligence through ML, deep learning, and NLP.", "source": "TechReview 2024"},
        {"title": "AI in Industry", "summary": "Industry adoption of AI grew 37% in 2023; top sectors: healthcare, finance, logistics.", "source": "McKinsey 2023"},
        {"title": "Ethical AI", "summary": "Bias, transparency, and accountability are the top ethical concerns in modern AI deployment.", "source": "IEEE Ethics 2024"},
    ],
    "climate change": [
        {"title": "Global Warming Trends", "summary": "Earth has warmed 1.1°C above pre-industrial levels; IPCC warns of 2°C threshold by 2040.", "source": "IPCC AR6 2022"},
        {"title": "Renewable Energy", "summary": "Solar and wind capacity grew 50% globally in 2023, displacing 800Mt of CO₂ emissions.", "source": "IEA 2023"},
        {"title": "Carbon Capture", "summary": "Direct air capture technology costs dropped 40% in 5 years but scale remains insufficient.", "source": "Nature Energy 2024"},
    ],
    "quantum computing": [
        {"title": "Quantum Supremacy", "summary": "Google's Sycamore performed a task in 200s that would take classical computers 10,000 years.", "source": "Google Research 2019"},
        {"title": "Quantum Cryptography", "summary": "Quantum key distribution offers theoretically unbreakable encryption using photon polarisation.", "source": "MIT Technology Review 2024"},
        {"title": "NISQ Era", "summary": "Noisy Intermediate-Scale Quantum devices offer 50-1000 qubits with limited error correction.", "source": "IBM Research 2023"},
    ],
}


# ===========================================================================
# ResearcherAgent
# ===========================================================================

class ResearcherAgent:
    """
    Finds relevant information on a topic using mock search results.
    Produces a structured research summary passed to the Writer.
    """

    name = "ResearcherAgent"
    role = "Information discovery and summarisation"

    def research(self, topic: str) -> dict:
        """
        Search for information on *topic* and return a structured summary.

        Input  : topic (str) — the research subject
        Output : research_package (dict) — structured for WriterAgent consumption
        """
        topic_lower = topic.lower()
        # Find the closest matching topic in mock DB
        matched_key = None
        for key in _MOCK_SEARCH_DB:
            if key in topic_lower or topic_lower in key:
                matched_key = key
                break

        articles = _MOCK_SEARCH_DB.get(matched_key, [
            {"title": "General Overview", "summary": f"No specific data found for '{topic}'. Using general knowledge.", "source": "Internal KB"}
        ])

        research_package = {
            "topic": topic,
            "articles": articles,
            "key_facts": [a["summary"] for a in articles],
            "sources": [a["source"] for a in articles],
            "researcher": self.name,
            "timestamp": _ts(),
        }

        print(f"\n[{self.name}] Research complete for topic: '{topic}'")
        print(f"  Found {len(articles)} articles from sources: {research_package['sources']}")
        return research_package

    def __repr__(self) -> str:
        return f"ResearcherAgent(role={self.role!r})"


# ===========================================================================
# WriterAgent
# ===========================================================================

class WriterAgent:
    """
    Drafts structured report sections from the ResearcherAgent's package.
    Receives the research_package dict and produces a draft_report dict.
    """

    name = "WriterAgent"
    role = "Report drafting from research summaries"

    def write(self, research_package: dict) -> dict:
        """
        Draft a report from *research_package*.

        Input  : research_package (dict) — from ResearcherAgent.research()
        Output : draft_report (dict) — structured for EditorAgent consumption
        """
        topic = research_package["topic"]
        articles = research_package["articles"]
        sources = research_package["sources"]

        # Introduction
        intro = (
            f"This report provides an overview of **{topic}**, drawing on "
            f"{len(articles)} authoritative sources. "
            f"The analysis covers key developments, trends, and implications."
        )

        # Body sections — one paragraph per article
        sections = []
        for i, article in enumerate(articles, 1):
            para = f"**{article['title']}**: {article['summary']} (Source: {article['source']})"
            sections.append({"section_number": i, "heading": article["title"], "body": para})

        # Conclusion
        conclusion = (
            f"In conclusion, {topic} represents a rapidly evolving domain with significant "
            f"implications for technology, society, and policy. "
            f"Continued research and cross-disciplinary collaboration are essential."
        )

        draft_report = {
            "topic": topic,
            "title": f"Report on {topic.title()}",
            "introduction": intro,
            "sections": sections,
            "conclusion": conclusion,
            "sources": sources,
            "draft_version": "1.0",
            "writer": self.name,
            "timestamp": _ts(),
        }

        print(f"\n[{self.name}] Draft report written: '{draft_report['title']}'")
        print(f"  Sections: {len(sections)}, Sources cited: {len(sources)}")
        return draft_report

    def __repr__(self) -> str:
        return f"WriterAgent(role={self.role!r})"


# ===========================================================================
# EditorAgent
# ===========================================================================

class EditorAgent:
    """
    Reviews the WriterAgent's draft for clarity and completeness.
    Returns a final edited report with review notes.
    """

    name = "EditorAgent"
    role = "Draft review for clarity and completeness"

    _MIN_SECTIONS = 2
    _MIN_SOURCES = 1

    def edit(self, draft_report: dict) -> dict:
        """
        Review and refine *draft_report*.

        Input  : draft_report (dict) — from WriterAgent.write()
        Output : final_report (dict) — polished, review-noted report
        """
        issues = []
        suggestions = []

        # Completeness checks
        if len(draft_report.get("sections", [])) < self._MIN_SECTIONS:
            issues.append("Insufficient sections — report needs at least 2 body sections.")
            suggestions.append("Add more research to expand the body.")

        if len(draft_report.get("sources", [])) < self._MIN_SOURCES:
            issues.append("Missing source citations.")
            suggestions.append("Ensure all facts are backed by cited sources.")

        if not draft_report.get("introduction", "").strip():
            issues.append("Introduction is missing or empty.")
            suggestions.append("Write a clear introductory paragraph.")

        if not draft_report.get("conclusion", "").strip():
            issues.append("Conclusion is missing.")
            suggestions.append("Add a summarising conclusion paragraph.")

        # Clarity enhancements
        edited_sections = []
        for section in draft_report.get("sections", []):
            # Wrap long lines for readability
            edited_body = textwrap.fill(section["body"], width=100)
            edited_sections.append({**section, "body": edited_body})

        status = "APPROVED" if not issues else "NEEDS_REVISION"

        final_report = {
            **draft_report,
            "sections": edited_sections,
            "review_status": status,
            "issues_found": issues,
            "editorial_suggestions": suggestions,
            "draft_version": "1.1 (edited)",
            "editor": self.name,
            "timestamp": _ts(),
        }

        print(f"\n[{self.name}] Editorial review complete.")
        print(f"  Status   : {status}")
        print(f"  Issues   : {len(issues)}")
        if issues:
            for iss in issues:
                print(f"    ⚠ {iss}")
        else:
            print(f"  ✓ Report meets quality standards.")
        return final_report


# ===========================================================================
# Crew Runner
# ===========================================================================

def run_crew(topic: str) -> dict:
    """Orchestrate the full Researcher → Writer → Editor pipeline."""
    print("\n" + "=" * 70)
    print(f"  RESEARCH & REPORT CREW — Topic: '{topic}'")
    print("=" * 70)

    researcher = ResearcherAgent()
    writer = WriterAgent()
    editor = EditorAgent()

    # Pipeline
    research_package = researcher.research(topic)
    draft_report = writer.write(research_package)
    final_report = editor.edit(draft_report)

    # Print final report
    print("\n" + "─" * 70)
    print(f"  FINAL REPORT: {final_report['title']}")
    print("─" * 70)
    print(f"\n  Introduction:\n  {final_report['introduction']}\n")
    for sec in final_report["sections"]:
        print(f"  Section {sec['section_number']} — {sec['heading']}:")
        print(f"  {sec['body']}\n")
    print(f"  Conclusion:\n  {final_report['conclusion']}\n")
    print(f"  Sources: {', '.join(final_report['sources'])}")
    print(f"  Review Status: {final_report['review_status']}")
    print("─" * 70)

    return final_report


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    for topic in ["Artificial Intelligence", "Climate Change", "Quantum Computing"]:
        run_crew(topic)
        print()
