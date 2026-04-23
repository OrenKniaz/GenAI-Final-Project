# This router defines all the 3 main agent actions: CONTINUE, SCHEDULE, and END.
from enum import Enum 

# Define an enumeration for the possible actions the agent can take.
class Action(str, Enum): 
    CONTINUE = "continue"
    SCHEDULE = "schedule"
    END = "end"

# A simple function that decides which action to take based on the message. 
# It looks for keywords related to scheduling or ending the conversation.

# Note, this is temporary and very basic skeleton code.
def decide_action(message: str) -> Action:
    text = message.lower()

    if "schedule" in text or "interview" in text or "time" in text:
        return Action.SCHEDULE

    if "bye" in text or "stop" in text or "not interested" in text:
        return Action.END

    return Action.CONTINUE

# Example usage of the decide_action function with some test messages.
if __name__ == "__main__":
    examples = [
        "Can we schedule an interview?",
        "Bye, I am not interested anymore.",
        "I have some questions about the role.",
    ]

    for example in examples:
        print(example, "->", decide_action(example))