from ..core import History, Event, EventHandler
import copy
from typing import Any, List
from deepdiff import DeepHash
import sys


class InMemoryHistory(History):
    """
    A History that saves all events in RAM. Useful for academic purposes.
    For an application in production, it can generate a prohibitive cost of RAM memory.
    """

    def __init__(self):
        super().__init__()
        self.events: list[Event] = []
        self.hashes: dict[str, Any] = dict()

    async def getEventsAsync(self, filters: dict) -> List[Event]:
        res: list[Event] = []
        cursor = True
        if ('cursor' in filters):
            cursor = False
        for event in self.events:
            satisfyConditions = True
            if ('cursor' in filters):
                if (event.id == filters['cursor']):
                    cursor = True
                    continue
            if (not cursor):
                satisfyConditions = False
            if ('ids' in filters):
                if (not event.id in filters['ids']):
                    satisfyConditions = False
            if ('topics' in filters):
                if (not event.topic in filters['topics']):
                    satisfyConditions = False
            if ('times' in filters):
                if (not event.time in filters['times']):
                    satisfyConditions = False
            if ('valuesHashes' in filters):
                if (not (await self.hashAsync(event.value)) in filters['valuesHashes']):
                    satisfyConditions = False
            if ('minTime' in filters):
                if (event.initTime < filters['minTime']):
                    satisfyConditions = False
            if ('maxTime' in filters):
                if (event.time > filters['maxTime']):
                    satisfyConditions = False
            if ('limit' in filters):
                if (len(res) + 1 > filters['limit']):
                    break
            if (satisfyConditions):
                res.append(event)
        return res

    async def countOutsAsync(self, handlers: List[EventHandler], minTime: int = 0, maxTime: int = sys.maxsize) -> int:
        topics: set[str] = set()
        for h in handlers:
            for topic in h.publishedTopics:
                topics.add(topic)
        events = await self.getEventsAsync({'topics': list(topics), 'minTime': minTime, 'maxTime': maxTime})
        return len(events)

    async def hashAsync(self, obj: Any) -> str:
        hash = DeepHash(obj)[obj]
        if (not hash in self.hashes):
            self.hashes[hash] = obj
        return hash

    async def objByHashAsync(self, hash: str) -> Any:
        if (hash in self.hashes):
            return self.hashes[hash]
        else:
            raise Exception(f'Hash {hash} not found in history.')

    async def addEventAsync(self, event: Event) -> None:
        deepCopy = copy.deepcopy(event)
        self.hashes[await self.hashAsync(deepCopy)] = deepCopy
        self.events.append(deepCopy)
