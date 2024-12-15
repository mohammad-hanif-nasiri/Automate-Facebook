const windowContainer = document.querySelector("div.windows-container");

function viewWindow(sessionId) {
  window.open(window.location.origin + "/screenshot/window/" + sessionId);
}

async function terminateWindow(sessionId) {
  const response = await (
    await fetch(window.location.origin + "/terminate/window/" + sessionId)
  ).json();

  const message = response.message;
  const code = response.code;
  const type = response.type;

  return code == 200 ? true : false;
}

windowContainer.addEventListener(
  "click",
  async (event) => {
    const targetElement = event.target;

    if (targetElement.tagName == "BUTTON") {
      const windowElement = targetElement?.closest("div.window");
      let sessionId;

      if (windowElement && (sessionId = windowElement.dataset.sessionId))
        if (targetElement.classList.contains("view-window")) {
          viewWindow(sessionId);
        } else if (targetElement.classList.contains("terminate-window")) {
          if (confirm("Are you sure?") === true)
            if ((await terminateWindow(sessionId)) === true) {
              alert("Window successfully terminated!");

              windowElement.remove();
            } else alert("An error occured!");
        }
    }
  },
  false,
);
