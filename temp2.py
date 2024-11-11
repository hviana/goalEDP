from src.goalEDP.extensions.goal import BeliefsReviewer, GoalStatusPromoter, Goal, Action, Agent, GoalBroker, Conflict
from src.goalEDP.explainers.simple_explainer import SimpleExplainer
from src.goalEDP.storages.in_memory import InMemoryHistory
from src.goalEDP.core import Event
from src.goalEDP.extensions.web_gui import WebGUI

import random
import time
import requests
from datetime import date


segAgent = "Segmentation agent | "
class ReviewPurchase(BeliefsReviewer):
    def __init__(self):
        self.purchases:dict[str,list] = dict()
        # Call to superclass constructor
        super().__init__(
            desc=segAgent+"Review purchase data, for the premium segment", attrs=["purchase"])  # Attributes can be external events, inputted or not by a simulator. They can also be events that represent communication between agents.

    async def reviewBeliefs(self):
        # The event queue is cleared each time the entity is processed. Maybe you want to save the beliefs in an object variable.
        beliefs = dict()
        if ("purchase" in self.eventQueueByTopic):
            beliefs["client_id"] = self.eventQueueByTopic["purchase"][-1].value["client_id"]
            beliefs["amount"] = self.eventQueueByTopic["purchase"][-1].value["amount"]
            if(not beliefs["client_id"] in self.purchases):
                self.purchases[beliefs["client_id"]] = list()
            self.purchases[beliefs["client_id"]].append(beliefs["amount"])
            beliefs["avg"] = sum(self.purchases[beliefs["client_id"]]) / len(self.purchases[beliefs["client_id"]])
        return beliefs

class PremiumAddPromoter(GoalStatusPromoter):
    def __init__(self):
        super().__init__(
            desc=segAgent+"Promotes goal - add customer to premium segment", beliefs=["client_id", "amount", "avg"], promotionNames=["intention"])

    async def promoteOrDemote(self):
        promotions = dict()
        promotions["intention"] = False
        if ("amount" in self.eventQueueByTopic):
            if (self.eventQueueByTopic["amount"][-1].value) >= 1000:
                promotions["intention"] = True
        if ("avg" in self.eventQueueByTopic):
            if (self.eventQueueByTopic["avg"][-1].value >= 500):
                promotions["intention"] = True
        return promotions

class PremiumRemovePromoter(GoalStatusPromoter):
    def __init__(self):
        super().__init__(
            desc=segAgent+"Promotes goal - remove customer from the premium segment", beliefs=["client_id", "amount"], promotionNames=["intention"])

    async def promoteOrDemote(self):
        promotions = dict()
        promotions["intention"] = True
        if ("amount" in self.eventQueueByTopic):
            if (self.eventQueueByTopic["amount"][-1].value) >= 1000:
                promotions["intention"] = False
        if(promotions["intention"]):
            if ("avg" in self.eventQueueByTopic):
                if (self.eventQueueByTopic["avg"][-1].value >= 500):
                    promotions["intention"] = False
        return promotions
class InactiveAddPromoter(GoalStatusPromoter):
    def __init__(self):
        super().__init__(
            desc=segAgent+"Promotes goal - add customer to inactive segment", beliefs=["client_id", "date"], promotionNames=["intention"])

    async def promoteOrDemote(self):
        promotions = dict()
        if ("date" in self.eventQueueByTopic):
            if (self.eventQueueByTopic["date"][-1].value) < date(2023, 1, 1):
                promotions["intention"] = True
            else:
                promotions["intention"] = False
        return promotions

class InactiveRemovePromoter(GoalStatusPromoter):
    def __init__(self):
        super().__init__(
            desc=segAgent+"Promotes goal - remove customer from the inactive segment", beliefs=["client_id", "date"], promotionNames=["intention"])

    async def promoteOrDemote(self):
        promotions = dict()
        if ("date" in self.eventQueueByTopic):
            if (self.eventQueueByTopic["date"][-1].value) > date(2023, 1, 1):
                promotions["intention"] = True
            else:
                promotions["intention"] = False
        return promotions

class PremiumAddAction(Action):
    def __init__(self):
        super().__init__(
            desc=segAgent+"Action to add customer to the premium segment", beliefs=["client_id"])

    async def procedure(self) -> None:
        requests.post('/comm', json=[{"topic":"segment-update", "value":{"segment":"premium","client_id": self.eventQueueByTopic["client_id"][-1].value}}])
        print("Add customer to the premium segment: "+ self.eventQueueByTopic["client_id"][-1].value)

class PremiumRemoveAction(Action):
    def __init__(self):
        super().__init__(
            desc=segAgent+"Action to remove customer from the premium segment", beliefs=["client_id"])

    async def procedure(self) -> None:
        requests.post('/comm', json=[{"topic":"segment-update", "value":{"segment": "not-premium","client_id": self.eventQueueByTopic["client_id"][-1].value}}])
        print("Remove customer from the premium segment: "+ self.eventQueueByTopic["client_id"][-1].value)

class InactiveAddAction(Action):
    def __init__(self):
        super().__init__(
            desc=segAgent+"Action to add customer to the inactive segment", beliefs=["client_id"])

    async def procedure(self) -> None:
        requests.post('/comm', json=[{"topic":"segment-update", "value":{"segment": "inactive","client_id": self.eventQueueByTopic["client_id"][-1].value}}])
        print("Add customer to the premium segment: "+ self.eventQueueByTopic["client_id"][-1].value)

class InactiveRemoveAction(Action):
    def __init__(self):
        super().__init__(
            desc=segAgent+"Action to remove customer from the inactive segment", beliefs=["client_id"])

    async def procedure(self) -> None:
        requests.post('/comm', json=[{"topic":"segment-update", "value":{"segment": "not-inactive","client_id": self.eventQueueByTopic["client_id"][-1].value}}])
        print("Remove customer from the inactive segment: "+ self.eventQueueByTopic["client_id"][-1].value)
        
# Goals with highest priority are pursued first


class PremiumAddGoal(Goal):
    def __init__(self):
        super().__init__(desc=segAgent+"Add customer to the premium segment",
                         promoter=PremiumAddPromoter(), plan=[PremiumAddAction()], priority=0)
        
class PremiumRemoveGoal(Goal):
    def __init__(self):
        super().__init__(desc=segAgent+"remove customer from the premium segment",
                         promoter=PremiumRemovePromoter(), plan=[PremiumRemoveAction()], priority=0)
class InactiveAddGoal(Goal):
    def __init__(self):
        super().__init__(desc=segAgent+"Add customer to the inactive segment",
                         promoter=InactiveAddPromoter(), plan=[InactiveAddAction()], priority=0)
        
class InactiveRemoveGoal(Goal):
    def __init__(self):
        super().__init__(desc=segAgent+"remove customer from the inactive segment",
                         promoter=InactiveRemovePromoter(), plan=[InactiveRemoveAction()], priority=0)

premiumAddGoal = PremiumAddGoal()
premiumRemoveGoal = PremiumRemoveGoal()
inactiveAddGoal = InactiveAddGoal()
inactiveRemoveGoal = InactiveRemoveGoal()

segAgentInstance = Agent(desc="Segmentation agent", beliefsReviewers=[ReviewPurchase()], goals=[premiumAddGoal,premiumRemoveGoal,inactiveAddGoal, inactiveRemoveGoal], conflicts=[])

autAgent = "Automating agent | "

class ReviewCustomerCoupon(BeliefsReviewer):
    def __init__(self):
        # Call to superclass constructor
        super().__init__(
            desc=autAgent+"Review customer coupons", attrs=["segment-update", "client_id"]) 
    async def reviewBeliefs(self):
        # The event queue is cleared each time the entity is processed. Maybe you want to save the beliefs in an object variable.
        beliefs = dict()
        if ("segment-update" in self.eventQueueByTopic):
            beliefs["client_id"] = self.eventQueueByTopic["segment-update"][-1].value["client_id"]
            beliefs["segment"] = self.eventQueueByTopic["segment-update"][-1].value["segment"]
        return beliefs

class GiveFreeShippingCouponPromoter(GoalStatusPromoter):
    def __init__(self):
        super().__init__(
            desc=autAgent+"Promotes goal - give free shipping coupon", beliefs=["client_id"], promotionNames=["intention"])

    async def promoteOrDemote(self):
        promotions = dict()
        return promotions

class Give10PercentCouponPromoter(GoalStatusPromoter):
    def __init__(self):
        super().__init__(
            desc=autAgent+"Promotes goal - Give 10 percent coupon", beliefs=["client_id"], promotionNames=["intention"])

    async def promoteOrDemote(self):
        promotions = dict()
        return promotions

class GiveFreeShippingCouponAction(Action):
    def __init__(self):
        super().__init__(
            desc=autAgent+"Give free shipping coupon action", beliefs=["client_id"])

    async def procedure(self) -> None:
        print("Free shipping coupon: " +
              str(self.eventQueueByTopic["client_id"][-1].value))

class Give10PercentAction(Action):
    def __init__(self):
        super().__init__(
            desc=autAgent+"Give 10 percent action", beliefs=["client_id"])

    async def procedure(self) -> None:
        print("10 percent coupon: " +
              str(self.eventQueueByTopic["client_id"][-1].value))

class Give10PercentCoupon(Goal):
    def __init__(self):
        super().__init__(desc=autAgent+"10 percent action coupon",
                         promoter=Give10PercentCouponPromoter(), plan=[Give10PercentAction()], priority=0)
class GiveFreeShippingCouponGoal(Goal):
    def __init__(self):
        super().__init__(desc=autAgent+"Give free shipping coupon",
                         promoter=GiveFreeShippingCouponPromoter(), plan=[GiveFreeShippingCouponAction()], priority=0)

autAgentInstance = Agent(desc="utomating agent", beliefsReviewers=[ReviewCustomerCoupon()], goals=[Give10PercentCoupon, GiveFreeShippingCouponGoal], conflicts=[])

# Instantiates history to save events.
history = InMemoryHistory()

# Instantiates the event broker, which also controls the execution sequence
broker = GoalBroker(agents=[segAgentInstance, autAgentInstance], history=history)


broker.startProcess()

# Enter external events, from a simulator for example.
for n in range(1000):
    broker.inputExternalEvents([
        Event("purchase", {"client_id":random.choice([1,2,3,4,5,6,7,8,9]), "amount":random.choice([300,600,900,1200,1500,1800]), "date":date(random.randint(2021, 2024), 1, 1)})
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
