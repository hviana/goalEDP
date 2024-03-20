import os
from abc import abstractmethod
from ..core import EventHandler, Event, EventBroker, History
from typing import Any, List
import asyncio
import nest_asyncio
from concurrent.futures import ThreadPoolExecutor
import traceback
nest_asyncio.apply()


class BeliefsReviewer(EventHandler):
    """  
    Represents a Belief Review Function.
    """

    def __init__(self, desc: str, attrs: List[str]):
        """
        Constructor:
        @param desc: Entity description. Do not use the same descriptions for different entities.
        @param attrs: Attributes that the entity will use, example: ['commChannel.attr1', 'environment.attr2', ...].
                      These attributes are incoming external event topics.
        """
        desc = "Beliefs Reviewer: " + desc
        super().__init__(desc=desc)
        self.subscribe(attrs)

    @abstractmethod
    async def reviewBeliefs(self) -> dict[str, Any]:
        """
        Review beliefs.
        You must go through "self.eventQueueByTopic" to read attributes information.
        @return: A dictionary with the new beliefs, example:   {
                                                                'cat1.belief1': True,
                                                                'cat2.belief2': 1,
                                                                ...
                                                                }
        """
        pass

    async def handleAsync(self) -> List[Event]:
        events = list()
        beliefs = await self.reviewBeliefs()
        for topic in beliefs:
            events.append(Event(topic, beliefs[topic]))
        return events


class GoalStatusPromoter(EventHandler):
    """
    Represents a Goal Status Promoter.
    """

    def __init__(self, desc: str, beliefs: List[str], promotionNames: List[str]):
        """
        Constructor:
        @param desc: Entity description. Do not use the same descriptions for different entities.
        @param beliefs: Beliefs that the entity will use, example: ['cat1.belief1', 'cat2.belief2', ...].
                        These beleifs are incoming event topics.
        @param promotions: Status promotions names that may appear, for example: ['desire', 'intention'].
        """
        desc = "Goal Status Promoter: " + desc
        super().__init__(
            desc=desc)
        self.promotionNames = promotionNames
        self.subscribe(beliefs)

    @abstractmethod
    async def promoteOrDemote(self) -> dict[str, bool]:
        """
        Review beliefs.
        You must go through "self.eventQueueByTopic" to read beliefs information.
        @return: A dictionary with status promotions (True) or demotions (False), example:   
                                                                       {
                                                                        'desire': True,
                                                                        'intention': False,
                                                                        ...
                                                                        }
        """
        pass

    def promotionNameToTopic(self, promotionName: str) -> str:
        """
        Combine the entity description with the status promotions name to form a readable topic for explanations.
        @promotions: Status promotions name
        @return: Topic representing the status promotions.
        """
        return self.desc + ", promotion/demotion: " + promotionName

    async def handleAsync(self) -> List[Event]:
        events = list()
        promotions = await self.promoteOrDemote()
        for topic in promotions:
            events.append(
                Event(self.promotionNameToTopic(topic), promotions[topic]))
        return events


class Action(EventHandler):
    """
    Represents a Action.
    """

    def __init__(self, desc: str, beliefs: List[str] = []):
        """
        Constructor:
        @param desc: Entity description. Do not use the same descriptions for different entities.
        @param beliefs: Beliefs that action will read, example: ['cat1.belief1', 'cat2.belief2', ...].
                        Detail that actions only read beliefs, and do not change them.
                        These beliefs are incoming event topics.
        """
        desc = "Action: " + desc
        super().__init__(desc=desc)
        self.subscribe(beliefs)
        self.goals: List[Goal] = []

    async def handleAsync(self) -> List[Event]:
        events = list()
        toExecute = False
        for goal in self.goals:
            # Check only the last one
            if (goal.desc in self.eventQueueByTopic):
                if self.eventQueueByTopic[goal.desc][-1].value == True:
                    toExecute = True
                    break
        if toExecute:
            try:
                await self.procedure()
                events.append(Event(self.desc, "SUCCESS"))
            except Exception as e:
                events.append(Event(self.desc, "ERROR: " + str(e)))
        return events

    @abstractmethod
    async def procedure(self) -> None:
        """
        The computational procedure that represents the action.
        When the action procedure is executed, it launches an event with the topic "SUCCESS".
        If the procedure throws an exception, an "ERROR: "+ERROR_NAME event will be thrown.
        You must go through "self.eventQueueByTopic" to read beliefs information.
        """
        pass


class Goal(EventHandler):
    """
    Represents a Goal.
    """

    def __init__(self, desc: str, promoter: GoalStatusPromoter, plan: List[Action], priority: int = 0):
        """
        Constructor:
        @param desc: Entity description. Do not use the same descriptions for different entities.
        @param promoter: GoalStatusPromoter instance. All possible promotions statuses have to be "True" for the goal to be pursued.
        @param plan: Agent's plan, represented by a list of actions. Actions are performed in the order of the list.
        @param priority: Goal priority. The higher the number, the more the goal is prioritized and pursued first.
        """
        desc = "Goal: " + desc + ", Priority: " + str(priority)
        super().__init__(desc=desc)
        self.promoter = promoter
        for promotionName in self.promoter.promotionNames:
            self.subscribe([self.promoter.promotionNameToTopic(promotionName)])
        self.priority = priority
        self.plan = plan
        for action in self.plan:
            action.subscribe([self.desc])
            action.goals.append(self)

    async def handleAsync(self) -> List[Event]:
        events = list()
        finallyPromoted = True
        havePromotions = False
        thereIsConflict = False
        for promotionName in self.promoter.promotionNames:
            promotionTopic = self.promoter.promotionNameToTopic(promotionName)
            if (promotionTopic in self.eventQueueByTopic):
                havePromotions = True
                if self.eventQueueByTopic[promotionTopic][-1].value == False:
                    finallyPromoted = False
                    break
        for topic in self.eventQueueByTopic:
            # It's a topic of conflict
            if isinstance(self.eventQueueByTopic[topic][-1].value, list):
                if self.desc in self.eventQueueByTopic[topic][-1].value:
                    thereIsConflict = True
                    break
        if thereIsConflict:
            events.append(Event(self.desc, False))
        else:
            if havePromotions:
                events.append(Event(self.desc, finallyPromoted))
        return events


class Conflict(EventHandler):
    """
    Represents a Conflict.
    """

    def __init__(self, desc: str, conflictingGoals: list[Goal]):
        """
        Constructor:
        @param desc: Entity description. Do not use the same descriptions for different entities.
        @param conflictingGoals: Instances of goals that together represent a conflict. If conflict is detected, the goal with the highest priority is chosen, with the others discarded.
        """
        desc = "Conflict: " + desc
        super().__init__(desc=desc)
        self.conflictingGoals = conflictingGoals
        # This ordering is important for the conflict resolution mechanism (choosing the one with the highest priority and discarding the others)
        self.conflictingGoals.sort(key=lambda x: x.priority, reverse=True)
        for goal in self.conflictingGoals:
            goal.subscribe([self.desc])
            self.subscribe([goal.desc])

    async def handleAsync(self) -> List[Event]:
        events = list()
        conflict = True
        for goal in self.conflictingGoals:
            if goal.desc in self.eventQueueByTopic:
                if self.eventQueueByTopic[goal.desc][-1].value != True:
                    conflict = False
            else:
                conflict = False
        if conflict:
            events.append(Event(self.desc, list(
                map(lambda x: x.desc, self.conflictingGoals[1:]))))
        return events


class Agent:
    """
    Represents an agent
    """

    def __init__(self, desc: str, beliefsReviewers: list[BeliefsReviewer], goals: list[Goal], conflicts: list[Conflict] = list()):
        """
        Constructor:
        @param desc: Agent description.
        @param beliefsReviewers: List of belief reviewers.
        @param goals: List of goals.
        @param conflicts: List of conflicts
        """
        self.desc = desc
        self.goals = goals
        # This ordering is important for the preference mechanism between objectives (pursue those with highest priority first - highest numerical value in priority).
        self.goals.sort(key=lambda x: x.priority, reverse=True)
        self.conflicts = conflicts
        self.beliefsReviewers = beliefsReviewers
        self.deliberating = False


class GoalBroker(EventBroker):
    def __init__(self, agents: List[Agent], history: History, delay: float = 0.5):
        """
        Constructor:
        @param agents: List of Agents.
        @param history: History used to save events.
        @param delay: It is used to define the interval between one process cycle and another.
        """
        # max_workers is the number of threads
        self._executor = ThreadPoolExecutor(
            max_workers=(os.cpu_count() or 1)*2)
        handlers = list()
        for agent in agents:
            for beliefsReviewer in agent.beliefsReviewers:
                handlers.append(beliefsReviewer)
            for goal in agent.goals:
                handlers.append(goal)
                handlers.append(goal.promoter)
                for action in goal.plan:
                    handlers.append(action)
            for conflict in agent.conflicts:
                handlers.append(conflict)
        super().__init__(
            handlers=handlers, history=history, delay=delay)
        self.agents = agents

    async def _deliberateAgentAsync(self, agent: Agent) -> None:
        """
        This method represents the processing of an agent, in the correct order that its inference should happen.
        1 - Processes all of the agent's belief reviewers concurrently, and waits for them all to finish.
        2 - Processes all of the agent's goal statuses promoters concurrently, and waits for them all to finish.
        3 - Processes agent's goals one by one, sequentially, in the order defined by their respective priorities.
        4 - Processes all of the agent's conflicts concurrently, and waits for them all to finish.
        5 - Processes agent's goals again (as you now also have conflict information), one by one, sequentially, in the order defined by their respective priorities.
        6 - For each agent goal that is processed in step 5, its actions are executed sequentially, one after the other, to maintain the order in which they were specified in the goal.
        @param agent: Agent instance.
        """
        agent.deliberating = True
        try:
            self._processLayer(agent.beliefsReviewers)
            self._processLayer([goal.promoter for goal in agent.goals])
            for goal in agent.goals:  # It needs to be sequential here, due to the preference mechanism
                await self.processHandler(goal)
            self._processLayer(agent.conflicts)
            # You need to run the goasl 2 times. One before the conflicts and one after.
            for goal in agent.goals:  # It needs to be sequential here, due to the preference mechanism
                await self.processHandler(goal)
                # Performing the actions sequentially avoids problems. Allows you to create an execution order. Execute A, then B...
                for action in goal.plan:
                    await self.processHandler(action)
        except Exception as e:
            traceback.print_tb(e.__traceback__)
            agent.deliberating = False
        agent.deliberating = False

    def _processingCycle(self) -> None:
        """
        Processes all agents. The idea is that they are all processed concurrently.
        """
        for agent in self.agents:
            if (not agent.deliberating):
                self._executor.submit(
                    asyncio.run, self._deliberateAgentAsync(agent))
