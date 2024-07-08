from ..core import Explainer, Event, EventBroker, History, EventHandler
from typing import Any, List
from deepdiff import DeepDiff
import sys


class SimpleExplainer(Explainer):
    """
    A non-optimized explainer, for academic purposes. It serves as a reference to implement the explanation generating methods.
    """

    def __init__(self, eventBroker: EventBroker, history: History):
        super().__init__(eventBroker, history)

    async def causesOfAsync(self, effects: List[Event], minTime: int = 0, maxTime: int = sys.maxsize) -> List[Event]:
        causes: set[Event] = set()
        for effect in effects:
            for eventHandler in self.eventBroker.publishers([effect.topic]):
                for topic in eventHandler.subscribedTopics:
                    hist: List[Event] = await self.history.getEventsAsync({'topics': [topic], 'minTime': minTime, 'maxTime': maxTime})
                    cause = Event(topic=topic, value=None,
                                  time=0, initTime=0)
                    for e in hist:
                        if (e.time <= effect.initTime):
                            if (e.time > cause.time):
                                cause = e
                    causes.add(cause)
        return list(causes)

    def _includeVal(self, val: Any, valuesList: List[Any]):
        for item in valuesList:
            if (len(DeepDiff(val, item)) == 0):
                return True
        return False

    def _sumAllCounts(self, dictCount: dict):
        count = 0
        for conn in dictCount:
            for hash in dictCount[conn]:
                count += dictCount[conn][hash]
        return count

    def pubHandlers(self, events: List[Event]) -> List[EventHandler]:
        topics = set()
        for e in events:
            topics.add(e.topic)
        return self.eventBroker.publishers(list(topics))

    async def similarEventsAsync(self, events: List[Event], minTime: int = 0, maxTime: int = sys.maxsize) -> tuple[List[Event], List[EventHandler]]:
        similarEvents = set()
        for e in events:
            valHash = await self.history.hashAsync(e.value)
            similarEvents.update(await self.history.getEventsAsync({'topics': [e.topic], 'valuesHashes': [valHash], 'minTime': minTime, 'maxTime': maxTime}))
        return similarEvents

    async def possibleCausesAsync(self, effects: List[Event], minTime: int = 0, maxTime: int = sys.maxsize) -> dict[str, dict[str, float]]:
        counts: dict[str, dict[str, int]] = dict()
        probs: dict[str, dict[str, float]] = dict()
        sEffects = await self.similarEventsAsync(effects, minTime, maxTime)
        handlers = self.pubHandlers(effects)
        allOutHandlersEventsCount = await self.history.countOutsAsync(handlers, minTime, maxTime)
        for cause in await self.causesOfAsync(sEffects, minTime, maxTime):
            valHash = await self.history.hashAsync(cause.value)
            if (not cause.topic in counts):
                counts[cause.topic] = dict()
                probs[cause.topic] = dict()
            if (not valHash in counts[cause.topic]):
                counts[cause.topic][valHash] = 0
                probs[cause.topic][valHash] = 0
            counts[cause.topic][valHash] += 1
        for topic in counts:
            for valHash in counts[topic]:
                probs[topic][valHash] = counts[topic][valHash] / \
                    allOutHandlersEventsCount
        return probs

    async def effectsOfAsync(self, causes: List[Event], minTime: int = 0, maxTime: int = sys.maxsize) -> List[Event]:
        effects: set[Event] = set()
        for cause in causes:
            for subscriber in self.eventBroker.subscribers([cause.topic]):
                for topic in subscriber.publishedTopics:
                    events: List[Event] = await self.history.getEventsAsync({'topics': [topic], 'minTime': minTime, 'maxTime': maxTime})

                    effect = Event(topic=topic, value=None,
                                   time=0, initTime=sys.maxsize)
                    for e in events:
                        if (e.initTime >= cause.time):
                            if (e.initTime < effect.initTime):
                                effect = e
                    effects.add(effect)
        return list(effects)

    async def possibleEffectsAsync(self, causes: List[Event], minTime: int = 0, maxTime: int = sys.maxsize) -> dict[str, dict[str, float]]:
        probs: dict[str, dict[Any, float]] = dict()
        counts: dict[str, dict[str, int]] = dict()
        similarCauses = await self.similarEventsAsync(causes, minTime, maxTime)
        effects = await self.effectsOfAsync(similarCauses, minTime, maxTime)
        publishers = self.pubHandlers(effects)
        allOutHandlersEventsCount = await self.history.countOutsAsync(publishers, minTime, maxTime)
        for effect in effects:
            valHash = await self.history.hashAsync(effect.value)
            if (not effect.topic in counts):
                counts[effect.topic] = dict()
                probs[effect.topic] = dict()
            if (not valHash in counts[effect.topic]):
                counts[effect.topic][valHash] = 0
                probs[effect.topic][valHash] = 0
            counts[effect.topic][valHash] += 1
        for topic in counts:
            for valHash in counts[topic]:
                probs[topic][valHash] = counts[topic][valHash] / \
                    allOutHandlersEventsCount
        return probs

    def _lastByTime(self, hist: List[Event]) -> Event:
        last = hist[0]
        for h in hist:
            if (h.time > last.time):
                last = h
        return last

    def _firstByTime(self, hist: List[Event]) -> Event:
        first = hist[0]
        for h in hist:
            if (h.time < first.time):
                first = h
        return first

    def _avgDiff(self, times1: List[float], times2: List[float]) -> float:
        sum = 0
        maxLen = len(times1)
        if(maxLen == 0):
            return 0
        if (len(times2) < len(times1)):
            maxLen = len(times2)
        for index in range(maxLen):
            sum += abs(times1[index] - times2[index])
        return sum/maxLen

    async def _times(self, topic: str, minTime: int = 0, maxTime: int = sys.maxsize) -> List[float]:
        events: List[Event] = await self.history.getEventsAsync({'topics': [topic], 'minTime': minTime, 'maxTime': maxTime})
        return [e.time for e in events]

    async def _initTimes(self, topic: str, minTime: int = 0, maxTime: int = sys.maxsize) -> List[float]:
        events: List[Event] = await self.history.getEventsAsync({'topics': [topic], 'minTime': minTime, 'maxTime': maxTime})
        return [e.initTime for e in events]

    async def fillEffectAsync(self, causes: List[Event], topic: str, value: Any, minTime: int = 0, maxTime: int = sys.maxsize) -> Event:
        initTime = self._lastByTime(causes).time
        processingTimeAvg = self._avgDiff(await self._times(topic, minTime, maxTime), await self._initTimes(topic, minTime, maxTime))
        time = initTime + processingTimeAvg
        effect = Event(topic=topic, value=value,
                       initTime=initTime, time=time)
        return effect

    async def fillCauseAsync(self, effects: List[Event], topic: str, value: Any, minTime: int = 0, maxTime: int = sys.maxsize) -> Event:
        time = self._firstByTime(effects).time
        processingTimeAvg = self._avgDiff(await self._times(topic, minTime, maxTime), await self._initTimes(topic, minTime, maxTime))
        initTime = time - processingTimeAvg
        cause = Event(topic=topic, value=value,
                      initTime=initTime, time=time)
        return cause
