# This router defines all the 3 main agent actions: CONTINUE, SCHEDULE, and END.
# and decides which action to take based on advisors response.
# Defines a router decision class
from enum import Enum 
from dataclasses import dataclass

# import advisors to help decide action.
from app.modules.exit_advisor import should_end
from app.modules.info_advisor import should_provide_info
from app.modules.schedule_advisor import should_schedule



# Define an enumeration for the possible actions the agent can take.
class Action(str, Enum): 
    CONTINUE = "continue"
    SCHEDULE = "schedule"
    END = "end"

# Define the router decision class
@dataclass(frozen=True)
class RouterDecision:
    action: Action
    exit_match: bool
    schedule_match: bool
    info_match: bool

# A simple function that decides which action to take based on the advisors' responses and returns a RouterDecision info, not just action

def route_message(message: str) -> RouterDecision:
    exit_match = should_end(message)
    schedule_match = should_schedule(message)
    info_match = should_provide_info(message)

    if exit_match:
        action = Action.END
    elif schedule_match:
        action = Action.SCHEDULE
    else:
        action = Action.CONTINUE

    return RouterDecision(
        action=action,
        exit_match=exit_match,
        schedule_match=schedule_match,
        info_match=info_match,
    )

# simpler function that only returns the actual action without additional info (1st version basically)
def decide_action(message: str) -> Action:
    return route_message(message).action

# Example usage of the decide_action function with some test messages.
if __name__ == "__main__":
    examples = [
        "Can we schedule an interview?",
        "Bye, I am not interested anymore.",
        "I have some questions about the role.",
    ]

    for example in examples:
        print(example, "->", decide_action(example))