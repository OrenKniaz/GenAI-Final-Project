# temporary module to decide schedule action, to be turned agentic later.


def should_schedule(message: str) -> bool:
    text = message.lower()
    if "schedule" in text or "interview" in text or "time" in text:
        return True
    return False

if __name__ == "__main__":
    examples = [
        "Can we schedule an interview?",
        "I have some questions about the role.",
        "Bye, I am not interested anymore.",
    ]

    for example in examples:
        print(example, "->", should_schedule(example))