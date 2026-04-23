# temporary module to decide exit action, to be turned agentic later.

def should_end(message: str) -> bool:
    text = message.lower()
    if "bye" in text or "stop" in text or "not interested" in text:
        return True
    return False


if __name__ == "__main__":
    examples = [
        "Bye, I am done.",
        "I am not interested anymore.",
        "I still have questions about the role.",
    ]

    for example in examples:
        print(example, "->", should_end(example))