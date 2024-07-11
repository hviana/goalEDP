from src.goalEDP.extensions.goal import BeliefsReviewer, GoalStatusPromoter, Goal, Action, Agent, GoalBroker, Conflict
from src.goalEDP.explainers.simple_explainer import SimpleExplainer
from src.goalEDP.storages.in_memory import InMemoryHistory
from src.goalEDP.core import Event
from src.goalEDP.extensions.web_gui import WebGUI

import random
import time


# Describe how the agent works:
# The Agent has the following flow:
# 1) revise beliefs
# 2) promotes goals statuses
# 3) detects conflicts
# 4) pursues goals

segAgent = "Segmentation agent | "
autAgent = "Automating agent | "

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
    
class ReviewBatteryLevel(BeliefsReviewer):
    def __init__(self):
        super().__init__(
            desc="Review battery level", attrs=["battery"])

    async def reviewBeliefs(self):
        beliefs = dict()
        if ("battery" in self.eventQueueByTopic):
            beliefs["low battery level"] = self.eventQueueByTopic["battery"][-1].value["percentage"] < 30
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

class RechargeBatteryPromoter(GoalStatusPromoter):
    def __init__(self):
        super().__init__(
            desc="Promotes battery recharge goal statuses", beliefs=["low battery level"], promotionNames=["intention"])

    async def promoteOrDemote(self):
        # The event queue is cleared each time the entity is processed. Maybe you want to save the promotions in an object variable.
        promotions = dict()
        if ("low battery level" in self.eventQueueByTopic):
            if (self.eventQueueByTopic["low battery level"][-1].value):
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
        
class RechargeBatteryAction(Action):
    def __init__(self):
        super().__init__(
            desc="Recharge battery action")

    async def procedure(self) -> None:
        print("Recharging battery")

# Goals with highest priority are pursued first


class Rescue(Goal):
    def __init__(self):
        super().__init__(desc="Rescuing victims of accidents",
                         promoter=RescuePromoter(), plan=[RescueAction()], priority=0)
        
class Recharge(Goal):
    def __init__(self):
        super().__init__(desc="Recharging the battery if the level is low",
                         promoter=RechargeBatteryPromoter(), plan=[RechargeBatteryAction()], priority=1)

rescueGoal = Rescue()
rechargeGoal = Recharge()

class RechargeInsteadOfSaveConflict(Conflict):
    def __init__(self):
        super().__init__(
            desc="Recharge battery instead of saving victim", conflictingGoals=[rescueGoal, rechargeGoal])


agent1 = Agent(desc="Robot that saves victims", beliefsReviewers=[
               ReviewAccident(), ReviewBatteryLevel()], goals=[rescueGoal,rechargeGoal], conflicts=[RechargeInsteadOfSaveConflict()])

# Instantiates history to save events.
history = InMemoryHistory()

# Instantiates the event broker, which also controls the execution sequence
broker = GoalBroker(agents=[agent1], history=history)

broker.startProcess()

# Enter external events, from a simulator for example.
for n in range(1000):
    broker.inputExternalEvents([
        Event("accident", {"victims": [
            {"mmHg": [random.randint(10, 15), random.randint(5, 10)], "bpm":random.randint(50, 110)}], "coord": [random.randint(0, 100), random.randint(0, 100)], "smoke": random.randint(0, 100)}),
        Event("battery", {"percentage":random.randint(0, 100)})
    ])
    time.sleep(1)

# instantiates the explanation manager
explainer = SimpleExplainer(broker, broker.history)

# Instantiates the explanation generator web graphical interface.
interface = WebGUI(explainer)

# Starts the web graphical interface server.
# The IP and port will be printed on the terminal.
# You must open the respective ip and port in the browser.
interface.server.run()
