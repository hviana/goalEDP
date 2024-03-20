from flask import Flask, request, Response
import os
from ..core import Explainer, EventHandler, Event, CoreJSONEncoder
import json
from typing import Any, List, Self
from .indexTemplate import indexTemplate


class WebGUI:
    def generateData(self) -> str:
        return CoreJSONEncoder().encode({
            "handlers": self.explainer.eventBroker.handlers,
            "associations": self.explainer.eventBroker.associatedTopics()
        })

    def __init__(self, explainer: Explainer) -> None:
        self.explainer = explainer
        self.server = Flask(__name__)

        async def parseEvents(reqData: Any) -> List[Event]:
            if ("events" in reqData):
                events = list()
                for d in reqData["events"]:
                    events.append(Event(topic=d["topic"], value=d["value"],
                                  time=d["time"], initTime=d["initTime"], id=d["id"]))
                return events
            else:
                return await self.explainer.history.getEventsAsync(reqData["filters"])

        @self.server.route("/")
        def index():
            script_dir = os.path.dirname(__file__)
            with open(os.path.join(script_dir, 'index.js'), 'r') as file:
                script = file.read()
            with open(os.path.join(script_dir, 'index.css'), 'r') as file:
                css = file.read()
            return indexTemplate(script=script, data=self.generateData(), baseUrl=request.base_url, css=css)

        @self.server.route('/history_get_events', methods=['POST'])
        async def historyGet():
            filters = request.json
            hist: list[Event] = await self.explainer.history.getEventsAsync(filters)
            return CoreJSONEncoder().encode(hist)

        @self.server.route('/fill_cause', methods=['POST'])
        async def fillCause():
            reqData = request.json
            effects: List[Event] = await parseEvents(reqData)
            value = await self.explainer.history.objByHashAsync(reqData["valueHash"])
            cause = await self.explainer.fillCauseAsync(effects=effects, topic=reqData["topic"], value=value, minTime=reqData["minTime"], maxTime=reqData["maxTime"])
            return CoreJSONEncoder().encode(cause)

        @self.server.route('/fill_effect', methods=['POST'])
        async def fillEffect():
            reqData = request.json
            causes: List[Event] = await parseEvents(reqData)
            value = await self.explainer.history.objByHashAsync(reqData["valueHash"])
            effect = await self.explainer.fillEffectAsync(causes=causes, topic=reqData["topic"], value=value, minTime=reqData["minTime"], maxTime=reqData["maxTime"])
            return CoreJSONEncoder().encode(effect)

        @self.server.route('/effects_of', methods=['POST'])
        async def effectsOf():
            reqData = request.json
            causes: List[Event] = await parseEvents(reqData)
            effects = await self.explainer.effectsOfAsync(causes=causes, minTime=reqData["minTime"], maxTime=reqData["maxTime"])
            return CoreJSONEncoder().encode(effects)

        @self.server.route('/causes_of', methods=['POST'])
        async def causesOf():
            reqData = request.json
            effects: List[Event] = await parseEvents(reqData)
            causes = await self.explainer.causesOfAsync(effects=effects, minTime=reqData["minTime"], maxTime=reqData["maxTime"])
            return CoreJSONEncoder().encode(causes)

        @self.server.route('/possible_effects', methods=['POST'])
        async def possibleEffects():
            reqData = request.json
            causes: List[Event] = await parseEvents(reqData)
            pr = await self.explainer.possibleEffectsAsync(causes=causes, minTime=reqData["minTime"], maxTime=reqData["maxTime"])
            self.explainer.normalizeProbs(pr)
            return CoreJSONEncoder().encode(pr)

        @self.server.route('/possible_causes', methods=['POST'])
        async def possibleCauses():
            reqData = request.json
            effects: List[Event] = await parseEvents(reqData)
            pr = await self.explainer.possibleCausesAsync(effects=effects, minTime=reqData["minTime"], maxTime=reqData["maxTime"])
            self.explainer.normalizeProbs(pr)
            return CoreJSONEncoder().encode(pr)

        @self.server.route('/hashes_to_value', methods=['POST'])
        async def hashesToValue():
            prData = request.json
            hashesAndVAlues = await self.explainer.hashesToValue(prData)
            return CoreJSONEncoder().encode(hashesAndVAlues)

        @self.server.route('/value_to_hash', methods=['POST'])
        async def valueToHash():
            reqData = request.json
            hash = await self.explainer.history.hashAsync(reqData)
            return CoreJSONEncoder().encode(hash)
