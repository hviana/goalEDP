from abc import ABC, abstractmethod
from typing import Any, List
import asyncio
import uuid
import json
import time
import sys
from threading import Timer
from collections import deque


class Event:
    """
    This class represents an event that can be saved in the history.
    Its construction was designed to aid storage (by ids, and topics).
    In addition, it has relevant temporal information for analysis.
    """
    @staticmethod
    def genId() -> str:
        return uuid.uuid4().hex

    def __init__(self, topic: str, value: Any = None, time: int = 0, initTime: int = 0, id: str = ""):
        """
        Constructor:
        @param id: (optional/auto generated if empty) Unique identifier.
        @param topic: event topic.
        @param value: event value. Use only JSON-serializable variables. If you want to use complex structured data, use compositions with Python's dict structure.
        @param time: Time in nanoseconds that the event was output from handler.
        @param initTime: Time in nanoseconds that handler was started to be processed to generate this event.
        """
        if (id == ""):
            id = Event.genId()
        self.id = id
        self.topic = topic
        self.value = value
        self.time = time
        self.initTime = initTime

    def __iter__(self):
        v = self.value
        try:  # for objects
            v = dict(v)
        except:
            try:
                v = v.__dict__
            except:
                pass
        data = {
            'id': self.id,
            'topic': self.topic,
            'time':     self.time,
            'initTime': self.initTime,
            'value': v
        }
        for x, y in data.items():
            yield x, y

    def toJSON(self) -> str:
        """
        The toJSON method returns a JSON of the object.
        It is very important for communicating with a web interface.
        @return: object JSON.
        """
        return CoreJSONEncoder().encode(dict(self))

    def __str__(self) -> str:
        """
        Method for python to know how to convert the object to type "str".
        Useful for printouts.
        @return: object str.
        """
        return self.toJSON()


class EventHandler(ABC):
    """
    This class represents a EventHandler (Publish/Subscribe pattern).
    """

    def __init__(self, desc: str = ""):
        """
        Constructor:
        @param desc: handler description.
        """
        self.desc = desc
        self.eventQueueByTopic: dict[str, deque[Event]] = dict()
        self.subscribedTopics: set[str] = set()
        self.publishedTopics: set[str] = set()

    def clearEventQueue(self):
        """
        Clears the queue of input events
        """
        self.eventQueueByTopic = dict()

    def addEventToQueue(self, event: Event):
        """
        Adds an event to the input queue.
        Input queues are a dictionary organized by topics ("self.eventQueueByTopic"). 
        Each dictionary entry is a topic, which contains a queue of events from that topic.
        @param event: Event to be added to a queue.
        """
        if (not event.topic in self.eventQueueByTopic):
            self.eventQueueByTopic[event.topic] = deque()
        self.eventQueueByTopic[event.topic].append(event)

    def subscribe(self, topics: List[str]) -> None:
        """
        Subscribe to receive events from a topic.
        @param topics: topics to subscribe.
        """
        for t in topics:
            self.subscribedTopics.add(t)

    def unSubscribe(self, topics: List[str]) -> None:
        """
        Unsubscribe to receive events from a topic.
        @param topics: topics to unsubscribe.
        """
        for t in topics:
            self.subscribedTopics.remove(t)

    def publish(self, topics: List[str]) -> None:
        """
        Enters information that a topic is published by Handler.
        The EventBroker uses this method to automatically populate this information when the Handler publishes an event to a new topic.
        @param topics: topics to publish.
        """
        for t in topics:
            self.publishedTopics.add(t)

    @abstractmethod
    async def handleAsync(self) -> List[Event]:
        """
        This method is what describes when the handle will publish events.
        This method must return a list of events that will be published (or an empty list).
        In many cases this method can use information from the input event queues (in "self.eventQueueByTopic").
        @return: events to be published (A list of Event instances)
        """
        pass

    def __iter__(self):
        data = {
            'desc': self.desc,
            'subscribedTopics': list(self.subscribedTopics),
            'publishedTopics':     list(self.publishedTopics),
        }
        for x, y in data.items():
            yield x, y

    def toJSON(self) -> str:
        """
        The toJSON method returns a JSON of the object.
        It is very important for communicating with a web interface.
        @return: object JSON.
        """
        return CoreJSONEncoder().encode(dict(self))

    def __str__(self) -> str:
        """
        Method for python to know how to convert the object to type "str".
        Useful for printouts.
        @return: object str.
        """
        return self.toJSON()


class History(ABC):
    """
    This class represents a way to save events.
    """
    @abstractmethod
    def __init__(self):
        """
        Constructor:
        """

    @abstractmethod
    async def hashAsync(self, obj: Any) -> str:
        """
        To return a unique hash representing a value.
        This method needs to save the hash association with the object for future retrieval of the value.
        If two values are the same, the hash is the same.
        This method is useful because an event value often represents complex structured data.
        @param obj: value/obj.
        @return: obj/value hash.
        """
        pass

    @abstractmethod
    async def objByHashAsync(self, hash: str) -> Any:
        """
        Implements a way to recover a value by its hash.
        @param hash: Hash.
        @return: obj/value.
        """
        pass

    @abstractmethod
    async def addEventAsync(self, event: Event) -> None:
        """
        Save an event to the History.
        @param event: Instance of class Event.
        """
        pass

    @abstractmethod
    async def getEventsAsync(self, filters: dict) -> List[Event]:
        """
        @param filters: A dict structure that contains the filters to return the events.
                        Filters can be different for each implementation of this abstract class.
                        It is important that the implementations of this class describe the filters that can be used in this method.
                        Recommended filters:
                        {
                            'ids': (List) Event ids,
                            'topics': (List) topics,
                            'times': (List) Event times,
                            'valuesHashes': (List) event values hashes,
                            'minTime': Lower limit for time (in nanoseconds), compared to the initTime of events.
                            'maxTime': Upper limit for time (in nanoseconds), compared to the time of events
                            'limit': Maximum number of events to return,
                            'cursor': Data from the last element of history in a previous recovery. Used to create pagination. it is recommended to use the id.
                            ...
                        }
        @return: a list of saved events (Event instances List).
        """
        pass

    @abstractmethod
    async def countOutsAsync(self, handlers: List[EventHandler], minTime: int = 0, maxTime: int = sys.maxsize) -> int:
        """
        Increases the number of outputs from a handler.
        @param handlers: (List) EventHandler instances
        @param minTime: Minimum time (in nanoseconds) to consider the count.
        @param maxTime: Maximum time (in nanoseconds) to consider the count.
        @return: count of the number of outputs of all Handlers. The count is: for each Handler, consider all events from all topics that it publishes.
        """
        pass

    def addEvent(self, event: Event) -> None:
        """
        Wraps the "addEventAsync" method for synchronous calls
        """
        return asyncio.run(self.addEventAsync(event))

    def getEvents(self, filters: dict) -> list[Event]:
        """
        Wraps the "getEventsAsync" method for synchronous calls
        """
        return asyncio.run(self.getEventsAsync(filters))

    def countOuts(self, handlers: List[EventHandler], minTime: int = 0, maxTime: int = sys.maxsize) -> int:
        """
        Wraps the "countOutsAsync" method for synchronous calls
        """
        return asyncio.run(self.countOutsAsync(handlers))


class EventBroker(ABC):
    """
    The class manages the processing of Handlers and the delivery of events.
    This class encapsulates the processing cycle for processing handlers.
    It is useful when processing needs a means of synchronization.
    An example is when one layer of the system needs to be executed before another.
    """

    def publishers(self, topics: List[str]) -> List[EventHandler]:
        """
        Returns all handlers that publish one or more topics that are contained in the input topics.
        @param topics: List of input topics.
        @return: Handlers who are publishers.
        """
        publishers = set()
        for handler in self.handlers:
            for topic in topics:
                if (topic in handler.publishedTopics):
                    publishers.add(handler)
        return list(publishers)

    def subscribers(self, topics: List[str]) -> List[EventHandler]:
        """
        Returns all handlers that subscribe one or more topics that are contained in the input topics.
        @param topics: List of input topics.
        @return: Handlers who are subscribers.
        """
        subscribers = set()
        for handler in self.handlers:
            for topic in topics:
                if (topic in handler.subscribedTopics):
                    subscribers.add(handler)
        return list(subscribers)

    def getAllTopics(self) -> List[str]:
        """
        Returns all topics used by the system.
        @return: all topics.
        """
        topics = set()
        for handler in self.handlers:
            for topic in handler.subscribedTopics:
                topics.add(topic)
            for topic in handler.publishedTopics:
                topics.add(topic)
        return list(topics)

    def associatedTopics(self) -> dict[str, dict[str, List[str]]]:
        """
        Returns a dictionary that contains associations between topics.
        It is useful for building graphical interfaces.
        @return: associations, as in the example: {
                                                    'topic2': {
                                                                'causes': ['topic0', 'topic1'],
                                                                'effects': ['topic3', 'topic4']
                                                              },
                                                    ...
                                                   }
        """
        topics = self.getAllTopics()
        associations = dict()
        for topic in topics:
            associations[topic] = dict()
            associations[topic]["causes"] = set()
            associations[topic]["effects"] = set()
            for handler in self.handlers:
                if topic in handler.subscribedTopics:
                    associations[topic]["effects"] = associations[topic]["effects"].union(
                        handler.publishedTopics)
                if topic in handler.publishedTopics:
                    associations[topic]["causes"] = associations[topic]["causes"].union(
                        handler.subscribedTopics)
        for topic in associations:
            if ("causes" in associations[topic]):
                associations[topic]["causes"] = list(
                    associations[topic]["causes"])
            if ("effects" in associations[topic]):
                associations[topic]["effects"] = list(
                    associations[topic]["effects"])
        return associations

    def inputExternalEvents(self, events: List[Event]) -> None:
        """
        Allows you to enter an external events in Event Broker.
        @param events: List of input events. If event times are not filled in (has value 0), they will be filled in automatically.
        """
        for event in events:
            if (event.time == 0):
                event.time = time.time_ns()
            if (event.initTime == 0):
                event.initTime = event.time
            self.history.addEvent(event)
            for subscriber in self.subscribers([event.topic]):
                subscriber.addEventToQueue(event)

    def __init__(self, handlers: List[EventHandler], history: History, delay: float = 0.5):
        """
        Constructor:
        @param handlers: Handlers that will be managed by the Broker.
        @param history: History used to save events.
        @param delay: It is used to define the interval between one process cycle and another.
        """
        self.handlers = handlers
        self.history = history
        self.delay = delay
        self._timer = None
        self.runningInTimer = False

    def _processLayer(self, handlers: EventHandler) -> None:
        """
        Processes a list of handlers concurrently, and waits until they are all finished.
        Useful for processing a layer of a system.
        """
        handlersCalls = [self.processHandler(
            handler) for handler in handlers]
        asyncio.run(asyncio.gather(*handlersCalls))

    def _processingCycle(self) -> None:
        """
        This method describes how handlers are processed.
        Each call to this method is a cycle of system processing.
        In the default implementation, processes all handlers concurrently, and waits for them all to be processed to repeat the cycle.
        That is, there is no synchronous order.
        For other processors that extend this class, this method needs to be overridden correctly.
        """
        self._processLayer(self.handlers)

    def _setTimer(self):
        if self.runningInTimer:
            self._processingCycle()
            self._timer = Timer(
                self.delay, self._setTimer)
            self._timer.start()

    async def processHandler(self, handler: EventHandler) -> None:
        """
        Processes a Handler:
        1 - Determines the time processing began.
        2 - Processes the Handler.
        3 - Clears Handler input queues.
        4 - Determines the time that processing finished.
        5 - Fill times in Handler output events.
        6 - Defines that the Handler is a publisher of the output topics.
        7 - Adds the Handler's output events to the history.
        8 - Delivers output events from Handler to subscribers.
        """
        initTime = time.time_ns()
        events: list[Event] = await handler.handleAsync()
        handler.clearEventQueue()
        endTime = time.time_ns()
        for e in events:
            e.initTime = initTime
            e.time = endTime
            handler.publish([e.topic])
            await self.history.addEventAsync(e)
            for subscriber in self.subscribers([e.topic]):
                subscriber.addEventToQueue(e)

    def startProcess(self) -> None:
        """
        Starts calls to the method that defines the processing cycle ("_processingCycle").
        Such a method is called once after another, with a delay between these calls (defined by "delay" in the constructor)
        """
        self.runningInTimer = True
        self._setTimer()

    def stopProcess(self) -> None:
        """
        Stops calls to the processing cycle.
        """
        if (self._timer):
            self._timer.cancel()
        self.runningInTimer = False


class Explainer(ABC):
    """
    Represents an explanation generator.
    """

    def __init__(self, eventBroker: EventBroker, history: History):
        """
        Constructor:
        @param history: Object responsible for saving processing events.
        """
        self.history = history
        self.eventBroker = eventBroker

    async def hashesToValue(self, prData: dict[str, dict[str, float]]) -> dict[str, Any]:
        """
        It has as input hash map and a list of hashes.
        It is capable of generating an association of hashes for causes/effects values.
        @param prData: probability hashs dict, ex:
                {
                  "topic1": {
                              "eventValueHash1" : probability,
                              ...
                            },
                  ...
                }
        @return: Map of hashes to causes or effect values, ex:
                { "eventValueHash1": value1, ... }
        """
        res = dict()
        for topic in prData:
            for eventValueHash in prData[topic]:
                res[eventValueHash] = await self.history.objByHashAsync(eventValueHash)
        return res

    def normalizeProbs(self, prData: dict[str, dict[str, float]]) -> None:
        """
        Normalizes probabilities in a range (0 to 1).
        Makes the changes in the same input dictionary.
        @param prData: probability hashs dict, ex:
                {
                  "topic1": {
                              "eventValueHash1" : probability,
                              ...
                            },
                  ...
                }
        """
        total = 0
        for topic in prData:
            for eventValueHash in prData[topic]:
                total += prData[topic][eventValueHash]
        for topic in prData:
            for eventValueHash in prData[topic]:
                prData[topic][eventValueHash] = prData[topic][eventValueHash]/total

    @abstractmethod
    async def causesOfAsync(self, effects: List[Event], minTime: int = 0, maxTime: int = sys.maxsize) -> List[Event]:
        """
        Causes for one or more effects.
        @param effects: Effect events for which causes will be calculated.
        @param minTime: Minimum time (in nanoseconds) to consider the calculation.
        @param maxTime: Maximum time (in nanoseconds) to consider the calculation.
        @return: A list of cause events.
        """
        pass

    @abstractmethod
    async def similarEventsAsync(self, events: List[Event], minTime: int = 0, maxTime: int = sys.maxsize) -> tuple[List[Event], List[EventHandler]]:
        """
        Similar events and handlers publishing these events.
        @param events: Events for which similars will be calculated. Similar events are events with the same topic and the same value.
        @param minTime: Minimum time (in nanoseconds) to consider the calculation.
        @param maxTime: Maximum time (in nanoseconds) to consider the calculation.
        @return: A list of similar events and a list of Handlers that publish these events.
        """
        pass

    @abstractmethod
    async def possibleCausesAsync(self, effects: List[Event], minTime: int = 0, maxTime: int = sys.maxsize) -> dict[str, dict[str, float]]:
        """
        Returns the probabilities of possible causes for one or more effects.
        @param effects: Effect events for which probabilities will be calculated.
        @param minTime: Minimum time (in nanoseconds) to consider the calculation.
        @param maxTime: Maximum time (in nanoseconds) to consider the calculation.
        @return: A probability dictionary, as in the example: 
                {
                  "topic1": {
                              "eventValueHash1" : probability,
                              ...
                           },
                  ...
                }
        """
        pass

    @abstractmethod
    async def effectsOfAsync(self, causes: List[Event], minTime: int = 0, maxTime: int = sys.maxsize) -> List[Event]:
        """
        Effects for one or more causes.
        @param causes: Cause events for which effects will be calculated.
        @param minTime: Minimum time (in nanoseconds) to consider the calculation.
        @param maxTime: Maximum time (in nanoseconds) to consider the calculation.
        @return: A list of effect events.
        """
        pass

    @abstractmethod
    async def possibleEffectsAsync(self, causes: List[Event], minTime: int = 0, maxTime: int = sys.maxsize) -> dict[str, dict[str, float]]:
        """
        Returns the probabilities of possible effects for one or more causes.
        @param causes: Cause events for which probabilities will be calculated.
        @param minTime: Minimum time (in nanoseconds) to consider the calculation.
        @param maxTime: Maximum time (in nanoseconds) to consider the calculation.
        @return: A probability dictionary, as in the example: 
                {
                  "topic1": {
                              "eventValueHash1" : probability,
                              ...
                           },
                  ...
                }
        """
        pass

    @abstractmethod
    async def fillEffectAsync(self, causes: List[Event], topic: str, value: Any, minTime: int = 0, maxTime: int = sys.maxsize) -> Event:
        """
        The probability dictionary returned by the methods contains only the topic and value of the events.
        This method helps to construct an effect in the form of an instance of the Event class, filling in the times that such an effect should have happened.
        @param causes: Causes used to calculate probabilities of effects.
        @param topic: Effect topic.
        @param value: Effect value.
        @param minTime: Minimum time (in nanoseconds) to consider the calculation.
        @param maxTime: Maximum time (in nanoseconds) to consider the calculation.
        @return: Effect of the shape of an Event instance.
        """
        pass

    @abstractmethod
    async def fillCauseAsync(self, effects: List[Event], topic: str, value: Any, minTime: int = 0, maxTime: int = sys.maxsize) -> Event:
        """
        The probability dictionary returned by the methods contains only the topic and value of the events.
        This method helps to construct an cause in the form of an instance of the Event class, filling in the times that such an cause should have happened.
        @param effects: Effects used to calculate probabilities of causes.
        @param topic: Cause topic.
        @param value: Cause value.
        @param minTime: Minimum time (in nanoseconds) to consider the calculation.
        @param maxTime: Maximum time (in nanoseconds) to consider the calculation.
        @return: Cause of the shape of an Event instance.
        """
        pass

    def causesOf(self, effect: Event, minTime: int = 0, maxTime: int = sys.maxsize) -> List[Event]:
        """
        Wraps the "causesOfAsync" method for synchronous calls
        """
        return asyncio.run(self.causesOfAsync(effect))

    def similarEvents(self, events: List[Event], minTime: int = 0, maxTime: int = sys.maxsize) -> tuple[List[Event], List[EventHandler]]:
        """
        Wraps the "similarEventsAsync" method for synchronous calls
        """
        return asyncio.run(self.similarEventsAsync(events))

    def possibleCauses(self, effects: List[Event], minTime: int = 0, maxTime: int = sys.maxsize) -> dict[str, dict[str, float]]:
        """
        Wraps the "possibleCausesAsync" method for synchronous calls
        """
        return asyncio.run(self.possibleCausesAsync(effects))

    def effectsOf(self, causes: List[Event], minTime: int = 0, maxTime: int = sys.maxsize) -> List[Event]:
        """
        Wraps the "effectsOfAsync" method for synchronous calls
        """
        return asyncio.run(self.effectsOfAsync(causes))

    def possibleEffects(self, causes: List[Event], minTime: int = 0, maxTime: int = sys.maxsize) -> dict[str, dict[Any, float]]:
        """
        Wraps the "possibleEffectsAsync" method for synchronous calls
        """
        return asyncio.run(self.possibleEffectsAsync(causes))

    def fillEffect(self, causes: List[Event], topic: str, value: Any, minTime: int = 0, maxTime: int = sys.maxsize) -> List[Event]:
        """
        Wraps the "fillEffectAsync" method for synchronous calls
        """
        return asyncio.run(self.fillEffectAsync(causes, topic, value))

    def fillCause(self, effects: List[Event], topic: str, value: Any, minTime: int = 0, maxTime: int = sys.maxsize) -> Event:
        """
        Wraps the "fillCauseAsync" method for synchronous calls
        """
        return asyncio.run(self.fillCauseAsync(effects, topic, value))


class CoreJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if (isinstance(o, Event) or isinstance(o, EventHandler)):
            return dict(o)
        else:
            return json.JSONEncoder.default(self, o)
