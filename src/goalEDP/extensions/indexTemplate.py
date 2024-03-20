def indexTemplate(baseUrl: str, data: str, script: str, css: str):
    return """
<!doctype html>
<html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Explainer Interface</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" crossorigin="anonymous">
        <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.11.8/dist/umd/popper.min.js" crossorigin="anonymous"></script>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.min.js" crossorigin="anonymous"></script>
        <script src="https://cdn.jsdelivr.net/npm/jsoneditor@10.0.1/dist/jsoneditor.min.js"></script>
        <link href="https://cdn.jsdelivr.net/npm/jsoneditor@10.0.1/dist/jsoneditor.min.css" rel="stylesheet">
        

    </head>
    <body>
<header>
<nav class="navbar navbar-expand-lg bg-dark navbar-dark fixed-top">
  <div class="container-fluid">
    <a class="navbar-brand" href="#">Explainer</a>
    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
      <span class="navbar-toggler-icon"></span>
    </button>
    <div class="collapse navbar-collapse" id="navbarNav">
      <ul class="navbar-nav">
        <li class="nav-item">
          <a class="nav-link" href="#" data-bs-toggle="modal" data-bs-target="#help">How to use</a>
        </li>
        <li class="nav-item dropdown">
          <a class="nav-link dropdown-toggle" href="#" id="manageExplainer" role="button" data-bs-toggle="dropdown" aria-expanded="false">
            Manage Explainer
          </a>
          <ul class="dropdown-menu dropdown-menu-dark" aria-labelledby="manageExplainer">
            <li><a class="dropdown-item" href="#" onclick="Drawer.setExpTimeRange()">Set explanation time range</a></li>
            <li><a class="dropdown-item" href="#" onclick="Drawer.addEvent()">Manually add event to explainer</a></li>
            <li><a class="dropdown-item" href="#" onclick="Drawer.drawExplanation()">Generate explanation</a></li>
            <li><a class="dropdown-item" href="#" onclick="Action.clearExplainer();alert('Clean explanation');">Clear explanation</a></li>
          </ul>
        </li>
        <li class="nav-item">
          <a class="nav-link" href="javascript:document.getElementById('about').scrollIntoView();">About</a>
        </li>
      </ul>
    </div>
  </div>
</nav>
</header>

<main class="mt-5">

  <section class="py-5 text-center container">
    <div class="row py-lg-5">
      <div class="col-lg-6 col-md-8 mx-auto">
        <h1 class="fw-light">Explainer Interface</h1>
      </div>
    </div>
  </section>

  <div class="album py-5 bg-light">
    <div class="container">
      <div class="row row-cols-1 row-cols-sm-2 row-cols-md-3 g-3" id="topics">
      </div>
    </div>
  </div>

</main>

<footer class="text-muted py-5">
  <div class="container">
    <p class="float-end mb-1">
      <a href="#">Back to top</a>
    </p>
    <p class="mb-1" id="about">Credits to the PETECO Causal and NOP research group at UTFPR - Curitiba.</p>
  </div>
</footer>

<div id="events" class="modal fade" tabindex="-1">
  <div class="modal-dialog modal-dialog-centered modal-dialog-scrollable">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title"></h5>
        <div class="spinner-grow text-primary" role="status"></div>
        <button type="button" class="btn btn-secondary ms-2" onclick="Drawer.openFilters();">Filters</button>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
      </div>
      <div class="modal-body">
        <ul class="list-group"></ul>
      </div>
    </div>
  </div>
</div>

<div id="explanation_drawer" class="modal fade" tabindex="-1">
  <div class="modal-dialog modal-dialog-centered modal-dialog-scrollable modal-fullscreen">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">Explanation
        </h5>
        <div class="spinner-grow text-primary" role="status"></div>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
      </div>
      <div class="modal-body">
      </div>
    </div>
  </div>
</div>

<div id="time_range" class="modal fade" tabindex="-1">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title"></h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
      </div>
      <div class="modal-body">
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-primary" data-bs-dismiss="modal" onclick="Action.setTimeRange(this.parentElement.parentElement.querySelector('.minTime').value,this.parentElement.parentElement.querySelector('.maxTime').value)">Set range</button>
        <button type="button" class="btn btn-danger" data-bs-dismiss="modal" onclick="Action.setTimeRange(undefined,undefined);">Clear</button>
      </div>
    </div>
  </div>
</div>

<div id="add_event" class="modal fade" tabindex="-1">
  <div class="modal-dialog modal-dialog-centered modal-dialog-scrollable">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">Add new event to explainer</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
      </div>
      <div class="modal-body">
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-primary" onclick="Action.createEventsFromData()">Add</button>
      </div>
    </div>
  </div>
</div>

<div id="topic_filters" class="modal fade" tabindex="-1">
  <div class="modal-dialog modal-dialog-centered modal-dialog-scrollable">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">Topic filters</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
      </div>
      <div class="modal-body">
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-primary" data-bs-dismiss="modal" onclick="Action.applyFilters()">Apply</button>
        <button type="button" class="btn btn-danger" data-bs-dismiss="modal" onclick="Action.clearFilters()">Clear filters</button>
      </div>
    </div>
  </div>
</div>

<div id="help" class="modal fade" tabindex="-1">
  <div class="modal-dialog modal-dialog-centered modal-dialog-scrollable">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">How to use</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
      </div>
      <div class="modal-body">
      <h2>Home screen</h2>
      <p class="text-justify">The home screen shows a list of topics that the system uses.
        By clicking on a topic, you can view the events launched by that topic.
        In the event view for a topic, you can scroll through the events.
        For a better view, you can use the topic filter.
      </p>
      <h2>Start an explanation</h2>
      <h3>1 - Select events</h3>
      <p class="text-justify">
        Each event you view can be added to the explanation by the arrow at the top of the event.
        You can also add an event that does not exist in the history to an explanation.
        To do this, use the "Manually add event to explainer" menu, within the "Manage Explainer" menu section.
        An event that does not exist in history can be interesting to find out why something did not happen.
        For example, if the event does not exist, its causes are the causes for the event not happening.
        In this case, it may also be useful to filter the explanation time range.
      </p>
      <h3>2 - Filter the explanation time range (optional)</h3>
      <p class="text-justify">
        You can filter the range in which you want to generate the explanation.
        This can be done in the "Set explanation time range" menu within the "Manage Explainer" section of the menu.
      </p>
      <h3>3 - Start explanation generation</h3>
      <p class="text-justify">
        To start the explanation, you need to access the "Generate explanation" menu within the "Manage Explainer" section.
        In the explanation generation window, you will see a graph.
        Each node in the graph is an event and the edges are probabilities. Above each node/event there is an arrow.
        In the arrow you have the possibility to expand the explanation with the available methods.
      </p>
      <h3>4 - Clear explanation (optional)</h3>
      <p class="text-justify">
        After generating an explanation, you may want to clear the web interface to start a new explanation.
        You can do this using the "Clear explanation" menu within the "Manage Explainer" section of the menu.
      </p>
      <h2>Comments</h2>
      <ul>
        <li>
          <p class="text-justify">
            When you refresh the page in the browser, you lose all the manipulations you made in the web interface.
          </p>
        </li>
        <li>
          <p class="text-justify">
            When restarting the Python application, you need to refresh the page in the browser.
          </p>
        </li>
        <li>
          <p class="text-justify">
            Event values are edited by a JSON editor.
            In the editor, there is a main vector. Each element of this vector is an event value.
            Be careful as the editor initializes with sample data. You need to delete these values.
          </p>
        </li>
      </ul>
      </div>
    </div>
  </div>
</div>

    <script>
    const baseUrl = "{baseUrl}";
    const data = {data};
    {script}
    </script>
    <style>
    {css}
    </style>
    </body>
</html>
""".format(script=script, data=data, baseUrl=baseUrl, css=css)
