# temporary module to decide info action, to be turned agentic later.

def should_provide_info(message: str) -> bool:
    text = message.lower()
    if "info" in text or "information" in text or "details" in text:
        return True
    return False

if __name__ == "__main__":
    examples = [
        "Can you provide more info about the role?",
        "I want more details about the position.",
        "I am not interested anymore.",
    ]

    for example in examples:
        print(example, "->", should_provide_info(example))