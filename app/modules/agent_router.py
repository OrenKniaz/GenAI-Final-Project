# This router defines all the 3 main agent actions: CONTINUE, SCHEDULE, and END.
# and decides which action to take based on advisors response.
from enum import Enum 

# import advisors to help decide action.
from app.modules.exit_advisor import should_end
from app.modules.info_advisor import should_provide_info
from app.modules.schedule_advisor import should_schedule

# Define an enumeration for the possible actions the agent can take.
class Action(str, Enum): 
    CONTINUE = "continue"
    SCHEDULE = "schedule"
    END = "end"

# A simple function that decides which action to take based on the advisors' responses. 

def decide_action(message: str) -> Action:
    # check ending advisor
    if should_end(message):
        return Action.END

    # check scheduling advisor
    if should_schedule(message):
         return Action.SCHEDULE

    # check info advisor
    if should_provide_info(message):
        return Action.CONTINUE

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