//JSON Pretty Print JS BEGIN
var JSON_PRETTY = function (string) {
  var pretty = {
    "parse": function (member) {
      return this
        [
          (member == undefined) ? "null" : member.constructor.name.toLowerCase()
        ](member);
    },
    "null": function (value) {
      return this["value"]("null", "null");
    },
    "array": function (value) {
      var results = "";
      for (var x = 0; x < value.length; x++) {
        results += "<li>" + this["parse"](value[x]) + "</li>";
      }
      return "[ " +
        ((results.length > 0) ? '<ul class="array">' + results + "</ul>" : "") +
        " ]";
    },
    "object": function (value) {
      var results = "";
      for (member in value) {
        results += "<li>" + this["value"]("object", member) + ": " +
          this["parse"](value[member]) + "</li>";
      }
      return "{ " +
        ((results.length > 0)
          ? '<ul class="object">' + results + "</ul>"
          : "") +
        " }";
    },
    "number": function (value) {
      return this["value"]("number", value);
    },
    "string": function (value) {
      return this["value"]("string", value);
    },
    "boolean": function (value) {
      return this["value"]("boolean", value);
    },

    "value": function (type, value) {
      if (/^(http|https):\/\/[^\s]+$/.test(value)) {
        return this["value"](
          type,
          '<a href="' + value + '" target="_blank">' + value + "</a>",
        );
      }
      return '<span class="' + type + '">' + value + "</span>";
    },
  };
  var parse = {
    "error": function (error) {
      return "<h1>Unable to parse JSON.</h1><p><h2>Error Message:</h2><textarea>" +
        error + "</textarea><br /><br /><h2>Response:</h2><textarea>" + string +
        "</textarea></p>";
    },
  };
  try {
    var output = pretty.parse(eval("(" + string + ")"));
  } catch (error) {
    var output = parse.error(error);
  }
  return output;
};
//JSON Pretty Print JS END

class Template {
  static timeInputChangeNs(el) {
    el.parentElement.querySelector('input[type="number"]').style.display =
      "block";
    el.parentElement.querySelector('input[type="datetime-local"]').style
      .display = "none";
  }
  static timeInputChangeDateTime(el) {
    el.parentElement.querySelector('input[type="number"]').style.display =
      "none";
    el.parentElement.querySelector('input[type="datetime-local"]').style
      .display = "block";
  }
  static inputDateTimeUpdate(el) {
    const timeNs = new Date(el.value).valueOf() * 1000000;
    el.parentElement.querySelector('input[type="number"]').value = timeNs;
  }
  static inputTimeNsUpdate(el) {
    const date = new Date(el.value / 1000000);
    date.setMinutes(date.getMinutes() - date.getTimezoneOffset());
    el.parentElement.querySelector('input[type="datetime-local"]').value = date
      .toISOString().slice(0, -1);
  }
  static timeInput(name) {
    return `
    <label class="form-label">${name}</label>
    <div class="input-group">
      <input class="form-control" type="datetime-local" step=".1" onchange="Template.inputDateTimeUpdate(this)"/>
      <input class="${name}" class="form-control" type="number" step="any" placeholder="time ns" style="display:none;" onkeyup="Template.inputTimeNsUpdate(this)"/>
      <button class="btn btn-outline-secondary" type="button" onclick="Template.timeInputChangeNs(this)">time ns</button>
      <button class="btn btn-outline-secondary" type="button" onclick="Template.timeInputChangeDateTime(this)">date+time</button>
    </div>
    `;
  }
  static event(event, hasMerged = false) {
    return `
    ${
      hasMerged
        ? `  
      <span class="badge rounded-pill bg-danger">
      merged
      </span>`
        : ""
    }
    <div class="print-json text-start event text-break ">${
      JSON_PRETTY(JSON.stringify(event))
    }</div>`;
  }
  static topic(topic) {
    return `
  <div class="col topic" id="${topic}">
    <div class="card shadow-sm">
      <div class="card-body">
      <p class="fw-bold card-text">Topic: ${topic}</p>
      <p class="card-text">Associated causes: ${
      Template.associateds(data.associations[topic].causes)
    }</p>
      <p class="card-text">Associated effects: ${
      Template.associateds(data.associations[topic].effects)
    }</p>
        <div class="d-flex justify-content-between align-items-center">
          <div class="btn-group">
            <button type="button" class="btn btn-sm btn-outline-secondary" onclick="Drawer.history('${topic}',false)">Published events</button>
          </div>
        </div>
      </div>
    </div>
  </div>
  `;
  }
  static associateds(associations) {
    var res = "<ul>";
    for (const a of associations) {
      res += `<li>${a}</li>`;
    }
    res += "</ul>";
    return res;
  }

  static eventListItem(event, actions = "add") {
    return `<li class="list-group-item overflow-auto" id="${event.id}">
    <div class="btn-group">
   ${
      actions == "add"
        ? `<a href="javascript:void(0)" class="dropdown-toggle" data-bs-toggle="dropdown" aria-expanded="false">
    </a>
    <ul class="dropdown-menu">
      <li><a class="dropdown-item" href="javascript:Action.addToExpEvents('${event.id}')">Add to events for explanations</a></li>
    </ul>
  </div>`
        : ""
    }
    ${Template.event(event)}`;
  }
  static jsonEditor(name) {
    return `<div class="${name} json-editor mt-1"></div>`;
  }
  static topicSelector() {
    var res = '<label class="form-label">Select topic</label>';
    res +=
      '<select class="form-select topic-selector" size="5" aria-label="Default select example">';
    res += `<option selected value="">---</option>`;
    const topics = Object.keys(data.associations);
    topics.sort();
    for (const t of topics) {
      res += `<option class="text-wrap" value="${t}">${t}</option>`;
    }
    res += "</select>";
    return res;
  }
}

class Drawer {
  static pageLimit = 10;
  static addEvent() {
    Drawer.showModal("add_event");
    document.querySelector("#add_event .modal-body").innerHTML = `
    ${Template.topicSelector()}
    ${Template.timeInput("initTime")}
    ${Template.timeInput("time")}
    <label class="form-label mt-2">Array of values (initialized with examples)</label>
    ${Template.jsonEditor("new-event-values")}
    `;
    Action.initJsonEditors(document.querySelector("#add_event .modal-body"), [
      "value1Example",
      { example2: 2 },
      true,
    ]);
  }
  static setExpTimeRange() {
    Drawer.showModal("time_range");
    document.querySelector("#time_range .modal-body").innerHTML = `
    ${Template.timeInput("minTime")}
    ${Template.timeInput("maxTime")}
    `;
    if ("minTime" in stateData["timeRange"]) {
      document.querySelector("#time_range .minTime").value =
        stateData["timeRange"]["minTime"];
      Template.inputTimeNsUpdate(
        document.querySelector("#time_range .minTime"),
      );
    }
    if ("maxTime" in stateData["timeRange"]) {
      document.querySelector("#time_range .maxTime").value =
        stateData["timeRange"]["maxTime"];
      Template.inputTimeNsUpdate(
        document.querySelector("#time_range .maxTime"),
      );
    }
  }
  static async drawExplanationLevel(method, eventIds, level, prevLevel) {
    document.querySelector("#explanation_drawer .spinner-grow").style.display =
      "inline-block";
    var methodRes = {
      prData: {},
      events: {},
    };
    const inputEvents = [];
    if (!method) {
      for (const eventId of eventIds) {
        const event = stateData["events"][eventId];
        if (!(event.topic in methodRes.events)) {
          methodRes.events[event.topic] = {};
        }
        const valHash = await Explainer.valueToHash(event.value);
        if (!(valHash in methodRes.events[event.topic])) {
          methodRes.events[event.topic][valHash] = [];
        }
        methodRes.events[event.topic][valHash].push(event);
      }
    } else {
      for (const eventId of eventIds) {
        inputEvents.push(stateData["events"][eventId]);
      }
      methodRes = await method(inputEvents);
    }
    if (Object.keys(methodRes.events) < 1) { //There are no causes or effects
      document.querySelector("#explanation_drawer .spinner-grow").style
        .display = "none";
      return;
    }
    var levelEl = document.getElementById(`level-${level}`);
    if (!levelEl) {
      var levelHtml =
        `<div class="text-center exp-level" id="level-${level}"></div>`;
      if (level > 0) {
        document.querySelector("#explanation_drawer .modal-body").innerHTML =
          levelHtml +
          document.querySelector("#explanation_drawer .modal-body").innerHTML;
      } else if (level < 0) {
        document.querySelector("#explanation_drawer .modal-body").innerHTML +=
          levelHtml;
      } else {
        document.querySelector("#explanation_drawer .modal-body").innerHTML =
          levelHtml;
      }
      levelEl = document.getElementById(`level-${level}`);
    }
    //draw events
    var levelContent = "";
    const merges = [];
    for (const topic in methodRes.events) {
      for (const valHash in methodRes.events[topic]) {
        if (!Array.isArray(methodRes.events[topic][valHash])) {
          methodRes.events[topic][valHash] = [methodRes.events[topic][valHash]];
        }
        for (const event of methodRes.events[topic][valHash]) {
          const eventElId = Drawer.eventElId(
            topic,
            valHash,
          );
          const eventEl = document.getElementById(
            eventElId,
          );
          if (!eventEl) {
            levelContent +=
              `<div class="exp-event d-inline-block border rounded p-1" level="${level}" event-id="${event.id}" id="${eventElId}" val-hash="${valHash}">
                    <a href="javascript:void(0)" class="dropdown-toggle" data-bs-toggle="dropdown" aria-expanded="false">
                    </a>
                    <ul class="dropdown-menu">
                      <li><a class="dropdown-item" href="javascript:Drawer.drawExplanationLevel(Explainer.possibleEffects,['${event.id}'],${
                level + 1
              },${level})">Metod: possibleEffects</a></li>
                      <li><a class="dropdown-item" href="javascript:Drawer.drawExplanationLevel(Explainer.possibleEffectsMaxProbabilities,['${event.id}'],${
                level + 1
              },${level})">Metod: possibleEffects  + Max probabilities</a></li>
                      <li><a class="dropdown-item" href="javascript:Drawer.drawExplanationLevel(Explainer.effectsOfWithProbabilities,['${event.id}'],${
                level + 1
              },${level})">Metods: effectsOf + possibleEffects</a></li>
                      <li><a class="dropdown-item" href="javascript:Drawer.drawExplanationLevel(Explainer.possibleCauses,['${event.id}'],${
                level - 1
              },${level})">Metod: possibleCauses</a></li>
                      <li><a class="dropdown-item" href="javascript:Drawer.drawExplanationLevel(Explainer.possibleCausesMaxProbabilities,['${event.id}'],${
                level - 1
              },${level})">Metod: possibleCauses + Max probabilities</a></li>
                      <li><a class="dropdown-item" href="javascript:Drawer.drawExplanationLevel(Explainer.causesOfWithProbabilities,['${event.id}'],${
                level - 1
              },${level})">Metods: causesOf + possibleCauses</a></li>
                    </ul>
                    <div class="event-container">${Template.event(event)}</div>
                  </div>
                  `;
          } else { //detect events to merge
            var hasMerged = false;
            const existingEvent =
              stateData["events"][eventEl.getAttribute("event-id")];
            event.id = existingEvent.id;
            if (existingEvent.initTime != event.initTime) {
              hasMerged = true;
            }
            if (existingEvent.time != event.time) {
              hasMerged = true;
            }
            if (hasMerged) {
              merges.push(event);
            }
          }
        }
      }
    }
    Drawer.updateStateEventsData(methodRes);
    levelEl.innerHTML += levelContent;

    if (method) {
      Drawer.calcLines(inputEvents, methodRes, prevLevel, level);
    }
    Drawer.mergeEvents(merges);
    Drawer.drawLines();
    document.querySelector("#explanation_drawer .spinner-grow").style
      .display = "none";
  }
  static updateStateEventsData(methodRes) {
    for (const topic in methodRes.events) { //update state data
      for (const valHash in methodRes.events[topic]) {
        for (const event of methodRes.events[topic][valHash]) {
          stateData["events"][event.id] = event;
        }
      }
    }
  }
  static calcLines(inputEvents, methodRes, prevLevel, level) {
    for (const origin of inputEvents) {
      const originEl = document.querySelector(
        `.exp-event[event-id="${origin.id}"]`,
      );
      if (prevLevel > level) { //causes pr
        for (
          const subscribedTopic of data.associations[origin.topic].causes
        ) {
          if (subscribedTopic in methodRes.events) {
            for (const valHash in methodRes.events[subscribedTopic]) {
              const targetElId = Drawer.eventElId(
                subscribedTopic,
                valHash,
              );
              const targetEl = document.getElementById(
                targetElId,
              );
              stateData["lines"][Drawer.lineId(targetEl.id, originEl.id)] = [
                targetEl.id,
                originEl.id,
                methodRes.prData[subscribedTopic][valHash],
                "cause",
              ];
            }
          }
        }
      } else {
        for (
          const publishedTopic of data.associations[origin.topic].effects
        ) {
          if (publishedTopic in methodRes.events) {
            for (const valHash in methodRes.events[publishedTopic]) {
              const targetElId = Drawer.eventElId(
                publishedTopic,
                valHash,
              );
              const targetEl = document.getElementById(
                targetElId,
              );
              stateData["lines"][Drawer.lineId(originEl.id, targetEl.id)] = [
                originEl.id,
                targetEl.id,
                methodRes.prData[publishedTopic][valHash],
                "effect",
              ];
            }
          }
        }
      }
    }
  }
  static mergeEvents(merges) {
    //merge event times alg:
    //mergedEvent elapsedTime = mergedEvent.time - mergedEvent.initTime
    //mergedEvent.initTime = max(times(connectedCauses)) where connectedCause.time > mergedEvent.initTime
    //mergedEvent.time  = min(initTimes(connectedEffects)) where connectedEffect.initTime < mergedEvent.time
    //if(mergedEvent.time > (mergedEvent.initTime + elapsedTime)){
    //  mergedEvent.time = mergedEvent.initTime + elapsedTime
    //}
    for (const mergedEvent of merges) {
      const elapsedTime = mergedEvent.time - mergedEvent.initTime;
      if (elapsedTime < 0) {
        elapsedTime = 0;
      }
      for (const lineId in stateData["lines"]) {
        var targetEvent = undefined;
        if (stateData["lines"][lineId][0] == mergedEvent.id) {
          targetEvent = stateData["events"][stateData["lines"][lineId][1]];
        } else if (stateData["lines"][lineId][1] == mergedEvent.id) {
          targetEvent = stateData["events"][stateData["lines"][lineId][0]];
        }
        if (targetEvent) {
          if (
            data.associations[mergedEvent.topic].causes.includes(
              targetEvent.topic,
            )
          ) {
            if (targetEvent.time > mergedEvent.initTime) {
              mergedEvent.initTime = targetEvent.time;
            }
          }
          if (
            data.associations[mergedEvent.topic].effects.includes(
              targetEvent.topic,
            )
          ) {
            if (targetEvent.initTime < mergedEvent.time) {
              mergedEvent.time = targetEvent.initTime;
            }
          }
        }
      }
      if (mergedEvent.time > (mergedEvent.initTime + elapsedTime)) {
        mergedEvent.time = mergedEvent.initTime + elapsedTime;
      }
      const eventEl = document.querySelector(
        `.exp-event[event-id="${mergedEvent.id}"]`,
      );
      eventEl.querySelector(".event-container").innerHTML = Template
        .event(mergedEvent, true);
    }
  }

  static drawLines() {
    document.querySelectorAll(".line").forEach((e) => e.remove());
    for (const lineId in stateData["lines"]) {
      var text = stateData["lines"][lineId][2];
      if (text.toString().length > 4) {
        text = text.toFixed(3);
      }
      Drawer.drawLine(
        stateData["lines"][lineId][0],
        stateData["lines"][lineId][1],
        `<span style="color:red;">${stateData["lines"][lineId][3]}:</span>` +
          text,
      );
    }
  }
  static lineId(originId, targetId) {
    return `${originId}-${targetId}`;
  }
  static eventElId(publishedTopic, valHash) {
    return `${publishedTopic}-${valHash}`;
  }

  static drawLine(origin, target, text) {
    const lineId = Drawer.lineId(
      origin.id,
      target.id,
    );
    const lineEl = document.getElementById(
      lineId,
    );
    if (!lineEl) {
      document.querySelector("#explanation_drawer .modal-body").innerHTML +=
        Drawer.connect(origin, target, "black", 1, text);
    }
  }

  static connect(div1Id, div2Id, color = "black", thickness = 1, text) { // draw a line connecting elements
    // bottom right
    var x1 = document.getElementById(div2Id).offsetLeft +
      document.getElementById(div2Id).offsetWidth / 2;
    var y1 = document.getElementById(div2Id).offsetTop +
      document.getElementById(div2Id).offsetHeight;
    // top right
    var x2 = document.getElementById(div1Id).offsetLeft +
      document.getElementById(div1Id).offsetWidth / 2;
    var y2 = document.getElementById(div1Id).offsetTop;
    // distance
    var length = Math.sqrt(((x2 - x1) * (x2 - x1)) + ((y2 - y1) * (y2 - y1)));
    // center
    var cx = ((x1 + x2) / 2) - (length / 2);
    var cy = ((y1 + y2) / 2) - (thickness / 2);
    // angle
    var angle = Math.atan2(y1 - y2, x1 - x2) * (180 / Math.PI);
    // make hr
    var htmlLine = "<div class='line' style='padding:0px; margin:0px; height:" +
      thickness + "px; background-color:" + color +
      "; line-height:1px; position:absolute; left:" + cx + "px; top:" + cy +
      "px; width:" + length + "px; -moz-transform:rotate(" + angle +
      "deg); -webkit-transform:rotate(" + angle + "deg); -o-transform:rotate(" +
      angle + "deg); -ms-transform:rotate(" + angle +
      "deg); transform:rotate(" + angle + "deg);'>" +
      `<span class="line-text">${text}</span>` +
      "</div>";
    //
    // alert(htmlLine);
    return htmlLine;
  }
  static showModal(elId) {
    const modal = bootstrap.Modal.getOrCreateInstance(
      document.getElementById(elId),
      {},
    );
    if (
      !document.getElementById(elId).classList.contains("show")
    ) {
      modal.show();
    }
  }
  static hideModal(elId) {
    const modal = bootstrap.Modal.getOrCreateInstance(
      document.getElementById(elId),
      {},
    );
    if (
      document.getElementById(elId).classList.contains("show")
    ) {
      modal.hide();
    }
  }
  static async drawExplanation() {
    Drawer.showModal("explanation_drawer");
    if (
      !document.getElementById(`level-1`) &&
      !document.getElementById(`level--1`)
    ) {
      Action.clearExplainer(false);
      await Drawer.drawExplanationLevel(
        null,
        stateData["expEvents"].map((e) => e.id),
        0,
      );
    }
  }
  static openFilters() {
    const topic = document.querySelector("#events").getAttribute("topic");
    document.querySelector("#topic_filters").setAttribute("topic", topic);
    document.querySelector("#topic_filters .modal-body").innerHTML = `${
      Template.timeInput("minTime")
    }
    ${Template.timeInput("maxTime")}
    <label class="form-label mt-2">Array of values (initialized with examples)</label>
    ${Template.jsonEditor("new-event-values")}
    `;
    Action.initJsonEditors(
      document.querySelector("#topic_filters .modal-body"),
      [
        "value1Example",
        { example2: 2 },
        true,
      ],
    );
    if (topic in stateData["topics"]) {
      if ("filters" in stateData["topics"][topic]) {
        if ("minTime" in stateData["topics"][topic]["filters"]) {
          document.querySelector("#topic_filters .minTime").value =
            stateData["topics"][topic]["filters"]["minTime"];
          Template.inputTimeNsUpdate(
            document.querySelector("#topic_filters .minTime"),
          );
        }
        if ("maxTime" in stateData["topics"][topic]["filters"]) {
          document.querySelector("#topic_filters .maxTime").value =
            stateData["topics"][topic]["filters"]["maxTime"];
          Template.inputTimeNsUpdate(
            document.querySelector("#topic_filters .maxTime"),
          );
        }
        if ("values" in stateData["topics"][topic]["filters"]) {
          document.querySelector("#topic_filters .json-editor").jsoneditor.set(
            stateData["topics"][topic]["filters"]["values"],
          );
        }
      }
    }
    //read state data
    Drawer.showModal("topic_filters");
  }
  static async history(topic, next = false) {
    document.querySelector("#events .spinner-grow").style.display = "block";
    Drawer.showModal("events");

    if (
      topic != document.querySelector("#events").getAttribute("topic", topic)
    ) {
      document.querySelector("#events .list-group").innerHTML = "";
      const refreshEl = document.getElementById("events-refresh");
      if (refreshEl) {
        refreshEl.remove();
      }
    } else if (
      !next && (document.querySelectorAll("#events .list-group li").length > 0)
    ) {
      document.querySelector("#events .spinner-grow").style.display = "none";
      return;
    }
    document.querySelector("#events").setAttribute("topic", topic);
    document.querySelector("#events .modal-title").innerHTML =
      `Topic: ${topic}`;

    Action.setTopicData(topic, undefined); //initialize filters
    const filters = { ...stateData["topics"][topic]["filters"] };
    if (!next) {
      delete filters["cursor"];
    }
    const res = await History.getEvents(filters);
    if (res.length > 0) {
      var resHtml = "";
      for (const r of res) {
        stateData["events"][r.id] = r;
        resHtml += Template.eventListItem(r);
      }
      filters["cursor"] = res[res.length - 1].id;
      Action.setTopicData(topic, filters);
      document.querySelector("#events .list-group").innerHTML += resHtml;
    }
    if (res.length < stateData["topics"][topic]["filters"]["limit"]) {
      const refreshEl = document.getElementById("events-refresh");
      if (!refreshEl) {
        document.querySelector("#events .modal-body").innerHTML += `
        <a id="events-refresh" class="btn btn-primary mt-1" href="javascript:Drawer.history('${topic}',true)">Refresh</a>
        `;
      }
    } else {
      const refreshEl = document.getElementById("events-refresh");
      if (refreshEl) {
        refreshEl.remove();
      }
    }
    document.querySelector("#events .spinner-grow").style.display = "none";
  }
  static randomColor() {
    const items = ["lightblue", "orange", "lightgreen", "pink"];
    return items[Math.floor(Math.random() * items.length)];
  }
  static scrollable(el, func) {
    el.addEventListener("scroll", async function () {
      if (el.scrolling) {
        return;
      }
      if (el.scrollTop === (el.scrollHeight - el.offsetHeight)) {
        el.scrolling = true;
        await func(el);
        el.scrolling = false;
      }
    });
  }
  static appendTopics() {
    for (const t in data.associations) {
      document.querySelector("#topics").innerHTML += Template.topic(
        t,
      );
    }
  }
}

class History {
  static async getEvents(filters) {
    return await (await fetch("/history_get_events", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(filters),
    })).json();
  }
}

class Explainer {
  static async fillCause(effects, topic, valueHash) {
    return await (await fetch("/fill_cause", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        events: effects,
        topic: topic,
        valueHash: valueHash,
        minTime: parseInt(stateData["timeRange"]["minTime"]) || 0,
        maxTime: parseInt(stateData["timeRange"]["maxTime"]) ||
          Number.MAX_SAFE_INTEGER * 1000000,
      }),
    })).json();
  }
  static async fillEffect(causes, topic, valueHash) {
    return await (await fetch("/fill_effect", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        events: causes,
        topic: topic,
        valueHash: valueHash,
        minTime: parseInt(stateData["timeRange"]["minTime"]) || 0,
        maxTime: parseInt(stateData["timeRange"]["maxTime"]) ||
          Number.MAX_SAFE_INTEGER * 1000000,
      }),
    })).json();
  }
  static async valueToHash(eventValue) {
    return await (await fetch("/value_to_hash", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(eventValue),
    })).json();
  }
  static async hashesToValue(prData) {
    return await (await fetch("/hashes_to_value", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(prData),
    })).json();
  }
  static async effectsOf(causes) {
    return await (await fetch("/effects_of", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        events: causes,
        minTime: parseInt(stateData["timeRange"]["minTime"]) || 0,
        maxTime: parseInt(stateData["timeRange"]["maxTime"]) ||
          Number.MAX_SAFE_INTEGER * 1000000,
      }),
    })).json();
  }
  static async possibleEffects(causes) {
    const prData = await (await fetch("/possible_effects", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        events: causes,
        minTime: parseInt(stateData["timeRange"]["minTime"]) || 0,
        maxTime: parseInt(stateData["timeRange"]["maxTime"]) ||
          Number.MAX_SAFE_INTEGER * 1000000,
      }),
    })).json();
    const events = {};
    for (const topic in prData) {
      events[topic] = {};
      for (const valHash in prData[topic]) {
        events[topic][valHash] = await Explainer.fillEffect(
          causes,
          topic,
          valHash,
        );
      }
    }
    return {
      prData: prData,
      events: events,
    };
  }
  //extra abstraction
  static async possibleEffectsMaxProbabilities(causes) {
    const prData = (await Explainer.possibleEffects(causes)).prData;
    const prMax = {};
    for (const topic in prData) {
      prMax[topic] = {};
      var maxHash = Object.keys(prData[topic])[0];
      for (const valHash in prData[topic]) {
        if (prData[topic][valHash] > prData[topic][maxHash]) {
          maxHash = valHash;
        }
      }
      prMax[topic][maxHash] = prData[topic][maxHash];
    }
    const events = {};
    for (const topic in prMax) {
      events[topic] = {};
      for (const valHash in prMax[topic]) {
        events[topic][valHash] = await Explainer.fillEffect(
          causes,
          topic,
          valHash,
        );
      }
    }
    return {
      prData: prMax,
      events: events,
    };
  }
  //extra abstraction
  static async effectsOfWithProbabilities(causes) {
    const effects = await Explainer.effectsOf(causes);
    const prDataAll = (await Explainer.possibleEffects(causes)).prData;
    const events = {};
    const prData = {};
    for (const e of effects) {
      if (!(e.topic in prData)) {
        prData[e.topic] = {};
        events[e.topic] = {};
      }
      const valHash = await Explainer.valueToHash(e.value);
      if (!(valHash in prData[e.topic])) {
        prData[e.topic][valHash] = prDataAll[e.topic][valHash];
        events[e.topic][valHash] = e;
      }
    }
    return {
      prData: prData,
      events: events,
    };
  }

  static async causesOf(effects) {
    return await (await fetch("/causes_of", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        events: effects,
        minTime: parseInt(stateData["timeRange"]["minTime"]) || 0,
        maxTime: parseInt(stateData["timeRange"]["maxTime"]) ||
          Number.MAX_SAFE_INTEGER * 1000000,
      }),
    })).json();
  }
  static async possibleCauses(effects) {
    const prData = await (await fetch("/possible_causes", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        events: effects,
        minTime: parseInt(stateData["timeRange"]["minTime"]) || 0,
        maxTime: parseInt(stateData["timeRange"]["maxTime"]) ||
          Number.MAX_SAFE_INTEGER * 1000000,
      }),
    })).json();
    const events = {};
    for (const topic in prData) {
      events[topic] = {};
      for (const valHash in prData[topic]) {
        events[topic][valHash] = await Explainer.fillCause(
          effects,
          topic,
          valHash,
        );
      }
    }
    return {
      prData: prData,
      events: events,
    };
  }
  //extra abstraction
  static async possibleCausesMaxProbabilities(effects) {
    const prMax = {};
    const prData = (await Explainer.possibleCauses(effects)).prData;
    for (const topic in prData) {
      prMax[topic] = {};
      var maxHash = Object.keys(prData[topic])[0];
      for (const valHash in prData[topic]) {
        if (prData[topic][valHash] > prData[topic][maxHash]) {
          maxHash = valHash;
        }
      }
      prMax[topic][maxHash] = prData[topic][maxHash];
    }
    const events = {};
    for (const topic in prData) {
      events[topic] = {};
      for (const valHash in prData[topic]) {
        events[topic][valHash] = await Explainer.fillCause(
          effects,
          topic,
          valHash,
        );
      }
    }
    return {
      prData: prData,
      events: events,
    };
  }
  //extra abstraction
  static async causesOfWithProbabilities(effects) {
    const causes = await Explainer.causesOf(effects);
    const prDataAll = (await Explainer.possibleCauses(effects)).prData;
    const events = {};
    const prData = {};
    for (const e of causes) {
      if (!(e.topic in prData)) {
        prData[e.topic] = {};
        events[e.topic] = {};
      }
      const valHash = await Explainer.valueToHash(e.value);
      if (!(valHash in prData[e.topic])) {
        prData[e.topic][valHash] = prDataAll[e.topic][valHash];
        events[e.topic][valHash] = e;
      }
    }
    return {
      prData: prData,
      events: events,
    };
  }
}

class Action {
  static async applyFilters() {
    const topic = document.querySelector("#topic_filters").getAttribute(
      "topic",
    );
    const minTime = parseInt(
      document.querySelector("#topic_filters .minTime").value,
    );
    const maxTime = parseInt(
      document.querySelector("#topic_filters .maxTime").value,
    );
    var values = [];
    try {
      values = document.querySelector("#topic_filters .new-event-values")
        .jsoneditor
        .get();
    } catch (e) {
    }
    if (!Array.isArray(values)) {
      values = [values];
    }
    const valuesHashes = [];
    for (const v of values) {
      valuesHashes.push(await Explainer.valueToHash(v));
    }
    const newFilters = { "topics": [topic], "limit": Drawer.pageLimit };
    if (minTime) {
      newFilters["minTime"] = minTime;
    }
    if (maxTime) {
      newFilters["maxTime"] = maxTime;
    }
    if (values.length > 0) {
      newFilters["values"] = values;
      newFilters["valuesHashes"] = valuesHashes;
    }
    Action.setTopicData(topic, newFilters);
    document.querySelector("#events .list-group").innerHTML = "";
    Drawer.history(topic);
  }
  static clearFilters() {
    const topic = document.querySelector("#topic_filters").getAttribute(
      "topic",
    );
    const newFilters = { "topics": [topic], "limit": Drawer.pageLimit };
    Action.setTopicData(topic, newFilters);
    document.querySelector("#events .list-group").innerHTML = "";
    Drawer.history(topic);
  }
  static createEventsFromData() {
    const topic = document.querySelector("#add_event .topic-selector").value;
    const initTime = parseInt(
      document.querySelector("#add_event .initTime").value,
    );
    const time = parseInt(document.querySelector("#add_event .time").value);
    var values = [];
    try {
      values = document.querySelector("#add_event .new-event-values").jsoneditor
        .get();
    } catch (e) {
    }
    if (!Array.isArray(values)) {
      values = [values];
    }
    if (!topic) {
      alert("Fill in the topic!");
      return;
    }
    if (!initTime) {
      alert("Fill in initTime!");
      return;
    }
    if (!time) {
      alert("Fill in time!");
      return;
    }
    if (values.length == 0) {
      alert("Fill in the values!");
      return;
    }
    for (const v of values) {
      const event = {
        id: crypto.randomUUID(),
        topic: topic,
        initTime: initTime,
        time: time,
        value: v,
      };
      stateData["events"][event.id] = event;
      stateData["expEvents"].push(event);
    }
    Drawer.hideModal("add_event");
  }
  static initJsonEditors(parent, initial = {}) {
    const options = {
      modes: ["code", "form", "text", "tree", "view"],
    };
    var el_list = parent.querySelectorAll(".json-editor"); // returns NodeList
    var el_array = [...el_list]; // converts NodeList to Array
    el_array.forEach((el) => {
      if (!(el.getAttribute("json-editor-initialized") == "true")) {
        el.setAttribute("json-editor-initialized", "true");
        const editor = new JSONEditor(el, options, initial);
        el.jsoneditor = editor;
      }
    });
  }
  static setTimeRange(minTime, maxTime) {
    if (!minTime) {
      delete stateData["timeRange"]["minTime"];
    } else {
      stateData["timeRange"]["minTime"] = parseInt(minTime);
    }
    if (!maxTime) {
      delete stateData["timeRange"]["maxTime"];
    } else {
      stateData["timeRange"]["maxTime"] = parseInt(maxTime);
    }
  }
  static setTopicData(topic, filters) {
    if (!(topic in stateData["topics"])) {
      stateData["topics"][topic] = {
        filters: { "topics": [topic], "limit": Drawer.pageLimit },
      };
    }
    if (filters != undefined) {
      stateData["topics"][topic]["filters"] = filters;
    }
  }
  static addToExpEvents(eventId) {
    const event = stateData["events"][eventId];
    if (stateData["expEvents"].length > 0) {
      for (const effect of stateData["expEvents"]) {
        if (effect.id == event.id) {
          alert("Event already added");
          return;
        }
      }
    }
    if (
      document.getElementById(`level-1`) || document.getElementById(`level--1`)
    ) {
      alert("Clear Explainer before adding another event.");
      return;
    }
    stateData["expEvents"].push(event);
  }

  static clearExplainer(clearQuery = true) {
    if (clearQuery) {
      stateData["expEvents"] = [];
    }
    stateData["lines"] = {};
    document.querySelector("#explanation_drawer .modal-body").innerHTML = "";
  }
}

const stateData = {
  "events": {},
  "expEvents": [],
  "topics": {}, //[topic]{eventsIds:[], filters:{}}
  "lines": {},
  "timeRange": {},
};

function initialize() {
  Drawer.appendTopics();
  Drawer.scrollable(
    document.querySelector("#events .modal-body"),
    (el) =>
      Drawer.history(
        document.querySelector("#events").getAttribute("topic"),
        true,
      ),
  );
}

document.addEventListener("DOMContentLoaded", (event) => {
  initialize();
  addEventListener("resize", (event) => {
    Drawer.drawLines();
  });
});
