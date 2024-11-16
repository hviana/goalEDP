from src.goalEDP.extensions.goal import BeliefsReviewer, GoalStatusPromoter, Goal, Action, Agent, GoalBroker, Conflict
from src.goalEDP.explainers.simple_explainer import SimpleExplainer
from src.goalEDP.storages.in_memory import InMemoryHistory
from src.goalEDP.core import Event
from src.goalEDP.extensions.web_gui import WebGUI

import threading

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
            if (self.eventQueueByTopic["date"][-1].value) < time.mktime(date(2023, 1, 1).timetuple()):
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
            if (self.eventQueueByTopic["date"][-1].value) > time.mktime(date(2023, 1, 1).timetuple()):
                promotions["intention"] = True
            else:
                promotions["intention"] = False
        return promotions

class PremiumAddAction(Action):
    def __init__(self):
        super().__init__(
            desc=segAgent+"Action to add customer to the premium segment", beliefs=["client_id"])

    async def procedure(self) -> None:
        eventValue = dict()
        eventValue["accessed_site"] = random.choice([True,False])
        eventValue["abandoned_cart"]=random.choice([True,False])
        eventValue["segments"] = ["premium"]
        eventValue["client_id"] = self.eventQueueByTopic["client_id"][-1].value
        #requests.post('http://127.0.0.1:5000/comm', json=[{"topic":"segmentation-update", "value":eventValue}])
        print("Add customer to the premium segment: "+ str(self.eventQueueByTopic["client_id"][-1].value))
        return [Event("segmentation-update", eventValue)]

class PremiumRemoveAction(Action):
    def __init__(self):
        super().__init__(
            desc=segAgent+"Action to remove customer from the premium segment", beliefs=["client_id"])

    async def procedure(self) -> None:
        eventValue = dict()
        eventValue["accessed_site"] = random.choice([True,False])
        eventValue["abandoned_cart"]=random.choice([True,False])
        eventValue["segments"] = ["not-premium"]
        eventValue["client_id"] = self.eventQueueByTopic["client_id"][-1].value
        #requests.post('http://127.0.0.1:5000/comm', json=[{"topic":"segmentation-update", "value":eventValue}])
        print("Remove customer from the premium segment: "+ str(self.eventQueueByTopic["client_id"][-1].value))
        return [Event("segmentation-update", eventValue)]

class InactiveAddAction(Action):
    def __init__(self):
        super().__init__(
            desc=segAgent+"Action to add customer to the inactive segment", beliefs=["client_id"])

    async def procedure(self) -> None:
        eventValue = dict()
        eventValue["accessed_site"] = random.choice([True,False])
        eventValue["abandoned_cart"]=random.choice([True,False])
        eventValue["segments"] = ["inactive"]
        eventValue["client_id"] = self.eventQueueByTopic["client_id"][-1].value
        #requests.post('http://127.0.0.1:5000/comm', json=[{"topic":"segmentation-update", "value":eventValue}])
        print("Add customer to the premium segment: "+ str(self.eventQueueByTopic["client_id"][-1].value))
        return [Event("segmentation-update", eventValue)]

class InactiveRemoveAction(Action):
    def __init__(self):
        super().__init__(
            desc=segAgent+"Action to remove customer from the inactive segment", beliefs=["client_id"])

    async def procedure(self) -> None:
        eventValue = dict()
        eventValue["accessed_site"] = random.choice([True,False])
        eventValue["abandoned_cart"]=random.choice([True,False])
        eventValue["segments"] = ["not-inactive"]
        eventValue["client_id"] = self.eventQueueByTopic["client_id"][-1].value
        #requests.post('http://127.0.0.1:5000/comm', json=[{"topic":"segmentation-update", "value":eventValue}])
        print("Remove customer from the inactive segment: "+ str(self.eventQueueByTopic["client_id"][-1].value))
        return [Event("segmentation-update", eventValue)]
        
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

segAgentInstance = Agent(desc="Segmentation agent", beliefsReviewers=[ReviewPurchase()], goals=[PremiumAddGoal(),PremiumRemoveGoal(),InactiveAddGoal(), InactiveRemoveGoal()], conflicts=[])

autAgent = "Automating agent | "

class ReviewCustomerCoupons(BeliefsReviewer):
    def __init__(self):
        # Call to superclass constructor
        super().__init__(
            desc=autAgent+"Review customer coupons", attrs=["segmentation-update"]) 
    async def reviewBeliefs(self):
        # The event queue is cleared each time the entity is processed. Maybe you want to save the beliefs in an object variable.
        beliefs = dict()
        if ("segmentation-update" in self.eventQueueByTopic):
            beliefs["client_id"] = self.eventQueueByTopic["segmentation-update"][-1].value["client_id"]
            beliefs["segments"] = self.eventQueueByTopic["segmentation-update"][-1].value["segments"],
            beliefs["abandoned_cart"] = self.eventQueueByTopic["segmentation-update"][-1].value["abandoned_cart"]
            beliefs["accessed_site"] = self.eventQueueByTopic["segmentation-update"][-1].value["accessed_site"]
        return beliefs

class GiveFreeShippingCouponPromoter(GoalStatusPromoter):
    def __init__(self):
        super().__init__(
            desc=autAgent+"Promotes goal - give free shipping coupon", beliefs=["client_id", "segments", "accessed_site"], promotionNames=["intention"])

    async def promoteOrDemote(self):
        promotions = dict()
        enterPremiumSegment = False
        outInactiveSegment = False
        accessedSite = False
        if ("segments" in self.eventQueueByTopic):
            enterPremiumSegment = (self.eventQueueByTopic["segments"][-1].value == "premium")
            outInactiveSegment = ("not-inactive" in self.eventQueueByTopic["segments"][-1].value[0])
        if ("accessed_site" in self.eventQueueByTopic):
            accessedSite = (self.eventQueueByTopic["accessed_site"][-1].value == True)
        if(accessedSite and (enterPremiumSegment or outInactiveSegment)):
            promotions["intention"] = True
        else:
            promotions["intention"] = False
        return promotions

class Give10PercentCouponPromoter(GoalStatusPromoter):
    def __init__(self):
        super().__init__(
            desc=autAgent+"Promotes goal - Give 10 percent coupon", beliefs=["client_id", "segments", "abandoned_cart"], promotionNames=["intention"])

    async def promoteOrDemote(self):
        promotions = dict()
        enterPremiumSegment = False
        abandonedCart = False
        if ("segments" in self.eventQueueByTopic):
            enterPremiumSegment = ("premium" in self.eventQueueByTopic["segments"][-1].value[0])
        if ("abandoned_cart" in self.eventQueueByTopic):
            abandonedCart = (self.eventQueueByTopic["abandoned_cart"][-1].value == True)
        if(abandonedCart and enterPremiumSegment):
            promotions["intention"] = True
        else:
            promotions["intention"] = False
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

autAgentInstance = Agent(desc="Automating agent", beliefsReviewers=[ReviewCustomerCoupons()], goals=[Give10PercentCoupon(), GiveFreeShippingCouponGoal()], conflicts=[])

# Instantiates history to save events.
history = InMemoryHistory()

# Instantiates the event broker, which also controls the execution sequence
broker = GoalBroker(agents=[segAgentInstance, autAgentInstance], history=history)

broker.startProcess()

# Enter external events, from a simulator for example.
for n in range(100):
    broker.inputExternalEvents([
        Event("purchase", {"client_id":random.choice([1,2,3,4,5,6,7,8,9]), "amount":random.choice([300,600,900,1200,1500,1800]), "date":time.mktime(date(random.randint(2021, 2024), 1, 1).timetuple())})
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

