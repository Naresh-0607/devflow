import logging

from app.config import settings
from app.models import EventType, SummaryType

logger = logging.getLogger(__name__)


def describe_event(event) -> str:
    """Turn a stored Git event into one human-readable line for the AI prompt."""
    import json

    try:
        payload = json.loads(event.payload_json or "{}")
    except json.JSONDecodeError:
        payload = {}

    event_type = event.event_type
    branch = payload.get("branch") or payload.get("to_branch") or payload.get("ref")
    message = payload.get("message")

    if event_type in (EventType.COMMIT, EventType.COMMIT.value):
        text = f"commit: {message or 'code changes'}"
        if branch:
            text += f" (branch {branch})"
        return text
    if event_type in (EventType.BRANCH_CHANGE, EventType.BRANCH_CHANGE.value):
        previous = payload.get("from_branch")
        if previous and branch:
            return f"switched branch {previous} -> {branch}"
        return f"checkout branch {branch or 'unknown'}"
    if event_type in (EventType.PUSH, EventType.PUSH.value):
        return f"pushed {branch or 'branch'} to remote"
    if event_type in (EventType.REPOSITORY_CREATED, EventType.REPOSITORY_CREATED.value):
        return "initialised repository"
    return f"{event_type} event"


def _fallback_summary(project_name: str, lines: list[str], summary_type: SummaryType) -> str:
    commits = [line for line in lines if line.startswith("commit:")]
    branches = [line for line in lines if "branch" in line and not line.startswith("commit:")]
    pushes = [line for line in lines if line.startswith("pushed")]

    if not lines:
        return f"No recorded activity for {project_name} in this period yet."

    parts: list[str] = []
    scope = {
        SummaryType.DAILY: "today",
        SummaryType.WEEKLY: "this week",
        SummaryType.PROJECT: "recently",
    }[summary_type]
    parts.append(
        f"You worked on {project_name} {scope}: {len(commits)} commit(s), "
        f"{len(branches)} branch change(s) and {len(pushes)} push(es)."
    )
    if commits:
        recent = [line.removeprefix("commit: ") for line in commits[-3:]]
        parts.append("Recent work: " + "; ".join(recent) + ".")
    if branches:
        current = branches[-1].split()[-1]
        parts.append(f"Current focus appears to be branch {current}.")
    return " ".join(parts)


async def generate_summary(
    project_name: str, lines: list[str], summary_type: SummaryType
) -> str:
    if not lines:
        return _fallback_summary(project_name, lines, summary_type)

    if settings.ai_enabled:
        try:
            import litellm

            prompt = (
                "You are DevFlow, a developer memory assistant. Summarise the Git activity "
                "below in 2-4 short sentences. Be concrete about the focus area and progress. "
                "Do not invent details that are not present. Return plain text only.\n\n"
                f"Project: {project_name}\n"
                f"Summary type: {summary_type.value}\n"
                "Events (oldest to newest):\n- " + "\n- ".join(lines)
            )
            response = await litellm.acompletion(
                model=settings.llm_model,
                api_key=settings.groq_api_key,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=300,
            )
            content = response.choices[0].message.content
            if content and content.strip():
                return content.strip()
        except Exception:  # pragma: no cover - provider/network failures
            logger.exception("LLM summary failed, using local fallback")

    return _fallback_summary(project_name, lines, summary_type)
