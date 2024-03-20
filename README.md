# goalEDP

Library for processing goal-oriented agents. Processing is done on an
event-driven mechanism. Events are saved to be used by explanation generating
methods.

## Contents

- [Sample application](#sample-application)
- [References](#references)
- [About](#about)

## Sample application

This package is published in the official Python repository. To install, use:

```
python3 -m pip install goalEDP
```

Application example:

```python
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
            beliefs["accident.hasAtLeastTwoVictims"] = len(
                self.eventQueueByTopic["accident"][-1].value["victims"]) >= 2
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
            desc="Promotes rescue goal statuses", beliefs=["accident.hasAtLeastTwoVictims", "accident.severityIsHigh"], promotionNames=["intention"])

    async def promoteOrDemote(self):
        # The event queue is cleared each time the entity is processed. Maybe you want to save the promotions in an object variable.
        promotions = dict()
        if ("accident.severityIsHigh" in self.eventQueueByTopic) and ("accident.hasAtLeastTwoVictims" in self.eventQueueByTopic):
            if (self.eventQueueByTopic["accident.severityIsHigh"][-1].value) or (self.eventQueueByTopic["accident.hasAtLeastTwoVictims"][-1].value):
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
          {"mmHg": [120, 80], "bpm":50}], "coord": [30, 40]})
])

# instantiates the explanation manager
explainer = SimpleExplainer(broker, broker.history)

# Instantiates the explanation generator web graphical interface.
interface = WebGUI(explainer)

# Starts the web graphical interface server.
# The IP and port will be printed on the terminal.
# You must open the respective ip and port in the browser.
interface.server.run()
```

## References

<a id="1">[1]</a> C. Castelfranchi and F. Paglieri. The role of beliefs in goal
dynamics: prolegomena to a constructive theory of intentions. Synthese, 155,
237–263, 2007. doi: https://doi.org/10.1007/s11229-006-9156-3

<a id="2">[2]</a> H. Jasinski and C. Tacla Denerating contrastive explanations
for BDI-based goal selection. url:
http://repositorio.utfpr.edu.br/jspui/handle/1/29522

<a id="3">[3]</a> J. M. Simão, C. A. Tacla, P. C. Stadzisz and R. F.
Banaszewski, "Notification Oriented Paradigm (NOP) and Imperative Paradigm: A
Comparative Study," Journal of Software Engineering and Applications, Vol. 5 No.
6, 2012, pp. 402-416. doi: https://www.doi.org/10.4236/jsea.2012.56047

## About

Author: Henrique Emanoel Viana, a Brazilian computer scientist, enthusiast of
web technologies, cel: +55 (41) 99999-4664. URL:
https://sites.google.com/view/henriqueviana

Improvements and suggestions are welcome!
