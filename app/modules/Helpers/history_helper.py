# For now this helper helps use entire history, later we might want to use summary \ smart semantic memory \ compaction if we have long conversations.

def format_conversation_history(history: list[str]) -> str:
    if not history:
        return "Recent conversation: none."

    lines = ["Recent conversation:"]
    for entry in history:
        lines.append(f"- {entry}")

    return "\n".join(lines)