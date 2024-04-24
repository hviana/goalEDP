from goalEDP.extensions.goal import BeliefsReviewer, GoalStatusPromoter, Goal, Action, Agent, GoalBroker, Conflict
from goalEDP.explainers.simple_explainer import SimpleExplainer
from goalEDP.storages.in_memory import InMemoryHistory
from goalEDP.core import Event
from goalEDP.extensions.web_gui import WebGUI


# Describe how the agent works:
# The Agent has the following flow:
# 1) revise beliefs
# 2) promotes goals statuses
# 3) detects conflicts
# 4) pursues goals

class ReviewAccident(BeliefsReviewer):
    def __init__(self):
        # Call to superclass constructor
        super().__init__(
            desc="Review accident data", attrs=["accident"])  # Attributes can be external events, inputted or not by a simulator. They can also be events that represent communication between agents.

    async def reviewBeliefs(self):
        # The event queue is cleared each time the entity is processed. Maybe you want to save the beliefs in an object variable.
        beliefs = dict()
        if ("accident" in self.eventQueueByTopic):
            # "-1" to get the last one in queue
            # Use only JSON-serializable variables as belief values.
            # In fact, in this framework all event values ​​must be serializable to JSON.
            # If you want to use complex structured data, use compositions with Python's dict structure.
            beliefs["accident.coord"] = self.eventQueueByTopic["accident"][-1].value["coord"]
            beliefs["accident.hasFire"] = self.eventQueueByTopic["accident"][-1].value["smoke"] > 50
            beliefs["accident.severityIsHigh"] = False
            for victim in self.eventQueueByTopic["accident"][-1].value["victims"]:
                if victim["bpm"] < 60 or victim["bpm"] > 100:
                    beliefs["accident.severityIsHigh"] = True
                if victim["mmHg"][0] > 14 or victim["mmHg"][1] < 6:
                    beliefs["accident.severityIsHigh"] = True
        return beliefs

# All goal statuses must be True for it to be pursued


class RescuePromoter(GoalStatusPromoter):
    def __init__(self):
        super().__init__(
            desc="Promotes rescue goal statuses", beliefs=["accident.hasFire", "accident.severityIsHigh"], promotionNames=["intention"])

    async def promoteOrDemote(self):
        # The event queue is cleared each time the entity is processed. Maybe you want to save the promotions in an object variable.
        promotions = dict()
        if ("accident.severityIsHigh" in self.eventQueueByTopic) and ("accident.hasFire" in self.eventQueueByTopic):
            if (self.eventQueueByTopic["accident.severityIsHigh"][-1].value) or (self.eventQueueByTopic["accident.hasFire"][-1].value):
                promotions["intention"] = True
            else:
                promotions["intention"] = False
        return promotions


class RescueAction(Action):
    def __init__(self):
        super().__init__(
            desc="Action to rescue victims", beliefs=["accident.coord"])

    async def procedure(self) -> None:
        print("Rescue at: " +
              str(self.eventQueueByTopic["accident.coord"][-1].value))

# Goals with highest priority are pursued first


class Rescue(Goal):
    def __init__(self):
        super().__init__(desc="Objective of rescuing victims of serious accidents",
                         promoter=RescuePromoter(), plan=[RescueAction()], priority=0)

# If conflict is detected, the goal with the highest priority is chosen, with the others discarded.
#
# class ConflictOne(Conflict):
#    def __init__(self):
#        super().__init__(
#            desc="Recharge battery instead of saving victim", conflictingGoals=[goalInstance1, goalInstance2])


agent1 = Agent(desc="Robot that saves victims", beliefsReviewers=[
               ReviewAccident()], goals=[Rescue()], conflicts=[])

# Instantiates history to save events.
history = InMemoryHistory()

# Instantiates the event broker, which also controls the execution sequence
broker = GoalBroker(agents=[agent1], history=history)

broker.startProcess()

# Enter external events, from a simulator for example.
broker.inputExternalEvents([
    Event("accident", {"victims": [
          {"mmHg": [120, 80], "bpm":50}], "coord": [30, 40], "smoke": 60})
])

# instantiates the explanation manager
explainer = SimpleExplainer(broker, broker.history)

# Instantiates the explanation generator web graphical interface.
interface = WebGUI(explainer)

# Starts the web graphical interface server.
# The IP and port will be printed on the terminal.
# You must open the respective ip and port in the browser.
interface.server.run()
