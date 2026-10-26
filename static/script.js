async function apiRequest(url, method = "GET", data = null) {
    const options = {
        method,
        headers: {},
        credentials: "same-origin"
    };

    if (data !== null) {
        options.headers["Content-Type"] = "application/json";
        options.body = JSON.stringify(data);
    }

    const response = await fetch(url, options);
    const contentType = response.headers.get("content-type") || "";
    let result;

    if (contentType.includes("application/json")) {
        result = await response.json();
    } else {
        const body = await response.text();
        result = {
            success: false,
            message: body || `Server returned HTTP ${response.status}`
        };
    }

    if (!response.ok) {
        throw new Error(result.message || `Request failed (${response.status})`);
    }

    return result;
}


/* =================================
   LOGIN
================================= */

function setupLogin() {

    const form =
        document.getElementById("loginForm");

    if (!form) return;

    form.addEventListener(
        "submit",
        async function(event) {

            event.preventDefault();

            const name =
                document
                    .getElementById("adminName")
                    .value
                    .trim();

            const password =
                document
                    .getElementById("password")
                    .value;

            const message =
                document.getElementById("message");

            message.textContent =
                "Logging in...";

            try {

                const result =
                    await apiRequest(
                        "/api/login",
                        "POST",
                        {
                            name: name,
                            password: password
                        }
                    );

                if (result.success) {

                    message.style.color =
                        "#22c55e";

                    message.textContent =
                        result.message;

                    setTimeout(
                        function() {

                            window.location.href =
                                "/contribution";

                        },
                        500
                    );

                } else {

                    message.style.color =
                        "#ef4444";

                    message.textContent =
                        result.message ||
                        "Login failed";

                }

            } catch (error) {

                message.style.color =
                    "#ef4444";

                message.textContent =
                    "Server connection error";

            }

        }
    );

}


/* =================================
   LOGOUT
================================= */

async function logoutUser() {

    await apiRequest(
        "/api/logout",
        "POST"
    );

    localStorage.removeItem("language_id");
    localStorage.removeItem("language_name");

    window.location.href = "/";

}


/* =================================
   CLOCK AND DATE
================================= */

function startLiveClock() {

    const clock =
        document.getElementById("liveClock");

    const date =
        document.getElementById("liveDate");

    if (!clock || !date) return;

    function update() {

        const now = new Date();

        clock.textContent =
            now.toLocaleTimeString();

        date.textContent =
            now.toLocaleDateString(
                undefined,
                {
                    weekday: "short",
                    year: "numeric",
                    month: "short",
                    day: "numeric"
                }
            );

    }

    update();

    setInterval(update, 1000);

}


/* =================================
   DASHBOARD
================================= */

function formatTime(totalSeconds) {

    totalSeconds =
        Number(totalSeconds || 0);

    const hours =
        Math.floor(totalSeconds / 3600)
            .toString()
            .padStart(2, "0");

    const minutes =
        Math.floor(
            (totalSeconds % 3600) / 60
        )
            .toString()
            .padStart(2, "0");

    const seconds =
        (totalSeconds % 60)
            .toString()
            .padStart(2, "0");

    return (
        hours +
        ":" +
        minutes +
        ":" +
        seconds
    );

}


async function loadDashboard() {

    const result =
        await apiRequest("/api/dashboard");

    if (result.error) {

        window.location.href = "/";
        return;

    }

    document
        .getElementById("activeDays")
        .textContent =
            result.active_days;

    document
        .getElementById("totalHours")
        .textContent =
            formatTime(result.total_seconds);

    document
        .getElementById("completedTopics")
        .textContent =
            result.completed_topics;

    document
        .getElementById("totalCodes")
        .textContent =
            result.total_codes;

    const user =
        await apiRequest("/api/user");

    document
        .getElementById("userWelcome")
        .textContent =
            "Welcome, " +
            user.name +
            " 👋";

}


/* =================================
   HEATMAP
================================= */

async function loadHeatmap() {

    const heatmap =
        document.getElementById("heatmap");

    if (!heatmap) return;

    const data =
        await apiRequest("/api/contributions");

    const contributionMap = {};

    data.forEach(function(item) {

        contributionMap[item.day] =
            item.count;

    });

    heatmap.innerHTML = "";

    const today = new Date();

    for (let i = 125; i >= 0; i--) {

        const date = new Date();

        date.setDate(
            today.getDate() - i
        );

        const day =
            date.toISOString()
                .split("T")[0];

        const count =
            contributionMap[day] || 0;

        const box =
            document.createElement("div");

        box.className =
            "heatmap-box";

        let level = 0;

        if (count === 1) level = 1;

        else if (count <= 3 && count > 1)
            level = 2;

        else if (count >= 4)
            level = 3;

        box.classList.add(
            "level-" + level
        );

        box.title =
            day +
            ": " +
            count +
            " saved codes";

        heatmap.appendChild(box);

    }

}


/* =================================
   LANGUAGES
================================= */

async function loadLanguages() {

    const grid =
        document.getElementById(
            "languageGrid"
        );

    if (!grid) return;

    const languages =
        await apiRequest("/api/languages");

    grid.innerHTML = "";

    languages.forEach(
        function(language) {

            const card =
                document.createElement("div");

            card.className =
                "language-card";

            card.innerHTML = `
                <h3>${language.name}</h3>

                <p>${language.category}</p>

                <div class="language-meta">
                    💾 ${language.saved_code_count} codes<br>
                    ⏱ ${formatTime(language.total_seconds)}
                </div>
            `;

            card.addEventListener(
                "click",
                function() {

                    localStorage.setItem(
                        "language_id",
                        language.id
                    );

                    localStorage.setItem(
                        "language_name",
                        language.name
                    );

                    window.location.href =
                        "/workspace";

                }
            );

            grid.appendChild(card);

        }
    );

}


function setupAddLanguage() {

    const button =
        document.getElementById(
            "addLanguageBtn"
        );

    if (!button) return;

    button.addEventListener(
        "click",
        async function() {

            const input =
                document.getElementById(
                    "newLanguage"
                );

            const name =
                input.value.trim();

            if (!name) {

                alert(
                    "Please enter language name"
                );

                return;

            }

            const result =
                await apiRequest(
                    "/api/languages",
                    "POST",
                    {
                        name: name
                    }
                );

            alert(result.message);

            input.value = "";

            loadLanguages();

        }
    );

}


/* =================================
   WORKSPACE
================================= */

let codingSessionId = null;
let codingSeconds = 0;
let timerInterval = null;


async function loadWorkspace() {

    const languageId =
        localStorage.getItem(
            "language_id"
        );

    const languageName =
        localStorage.getItem(
            "language_name"
        );

    if (!languageId) {

        window.location.href =
            "/contribution";

        return;

    }

    document
        .getElementById(
            "workspaceTitle"
        )
        .textContent =
            languageName +
            " Workspace";

    document
        .getElementById(
            "languageBadge"
        )
        .textContent =
            languageName;

    await loadTopics();

    await loadSavedCodes();

}


function updateTimerDisplay() {

    const timer =
        document.getElementById("timer");

    if (timer) {

        timer.textContent =
            formatTime(codingSeconds);

    }

}


async function saveCodingTime() {

    if (!codingSessionId) return;

    await apiRequest(
        "/api/session/update",
        "POST",
        {
            session_id:
                codingSessionId,

            elapsed_seconds:
                codingSeconds
        }
    );

}


function setupTimer() {

    const start =
        document.getElementById("startBtn");

    const pause =
        document.getElementById("pauseBtn");

    if (!start || !pause) return;


    start.addEventListener(
        "click",
        async function() {

            if (timerInterval) return;

            const languageId =
                Number(
                    localStorage.getItem(
                        "language_id"
                    )
                );

            if (!codingSessionId) {

                const result =
                    await apiRequest(
                        "/api/session/start",
                        "POST",
                        {
                            language_id:
                                languageId
                        }
                    );

                codingSessionId =
                    result.session_id;

            }

            timerInterval =
                setInterval(
                    function() {

                        codingSeconds++;

                        updateTimerDisplay();

                        if (
                            codingSeconds % 15 === 0
                        ) {

                            saveCodingTime();

                        }

                    },
                    1000
                );

        }
    );


    pause.addEventListener(
        "click",
        async function() {

            if (timerInterval) {

                clearInterval(
                    timerInterval
                );

                timerInterval = null;

            }

            await saveCodingTime();

            alert("Coding time saved");

        }
    );

}


/* =================================
   TOPICS
================================= */

async function loadTopics() {

    const languageId =
        localStorage.getItem(
            "language_id"
        );

    const topicList =
        document.getElementById(
            "topicList"
        );

    const topicSelect =
        document.getElementById(
            "codeTopic"
        );

    const result =
        await apiRequest(
            "/api/topics/" +
            languageId
        );

    topicList.innerHTML = "";

    if (topicSelect) {

        topicSelect.innerHTML =
            `<option value="">
                Select related topic
            </option>`;

    }

    let completed = 0;

    result.topics.forEach(
        function(item) {

            if (item.completed) {

                completed++;

            }

            const label =
                document.createElement(
                    "label"
                );

            const checkbox =
                document.createElement(
                    "input"
                );

            checkbox.type =
                "checkbox";

            checkbox.checked =
                item.completed === 1;

            checkbox.addEventListener(
                "change",
                async function() {

                    await apiRequest(
                        "/api/topics/update",
                        "POST",
                        {
                            language_id:
                                Number(
                                    languageId
                                ),

                            topic:
                                item.topic,

                            completed:
                                checkbox.checked
                        }
                    );

                    loadTopics();

                }
            );

            label.appendChild(
                checkbox
            );

            label.appendChild(
                document.createTextNode(
                    " " +
                    item.topic
                )
            );

            topicList.appendChild(
                label
            );


            if (topicSelect) {

                const option =
                    document.createElement(
                        "option"
                    );

                option.value =
                    item.topic;

                option.textContent =
                    item.topic;

                topicSelect.appendChild(
                    option
                );

            }

        }
    );

    const progress =
        result.topics.length > 0
            ? (
                completed /
                result.topics.length
            ) * 100
            : 0;

    document
        .getElementById(
            "progressText"
        )
        .textContent =
            completed +
            " of " +
            result.topics.length +
            " topics completed";

    document
        .getElementById(
            "progressFill"
        )
        .style.width =
            progress + "%";

}


/* =================================
   SAVE CODE
================================= */

function setupSaveCode() {

    const button =
        document.getElementById(
            "saveCodeBtn"
        );

    if (!button) return;

    button.addEventListener(
        "click",
        async function() {

            const languageId =
                Number(
                    localStorage.getItem(
                        "language_id"
                    )
                );

            const title =
                document
                    .getElementById(
                        "codeTitle"
                    )
                    .value
                    .trim() ||
                "Untitled Code";

            const topic =
                document
                    .getElementById(
                        "codeTopic"
                    )
                    .value;

            const code =
                document
                    .getElementById(
                        "codeArea"
                    )
                    .value;

            const message =
                document.getElementById(
                    "saveMessage"
                );

            if (!code.trim()) {

                message.style.color =
                    "#ef4444";

                message.textContent =
                    "Please write some code";

                return;

            }

            await saveCodingTime();

            const result =
                await apiRequest(
                    "/api/code/save",
                    "POST",
                    {
                        language_id:
                            languageId,

                        title:
                            title,

                        topic:
                            topic,

                        code:
                            code
                    }
                );

            if (result.success) {

                message.style.color =
                    "#22c55e";

                message.textContent =
                    "✓ Code saved";

                document
                    .getElementById(
                        "codeTitle"
                    )
                    .value = "";

                document
                    .getElementById(
                        "codeArea"
                    )
                    .value = "";

                await loadSavedCodes();

            }

        }
    );

}


/* =================================
   SAVED CODES
================================= */

async function loadSavedCodes() {

    const languageId =
        localStorage.getItem(
            "language_id"
        );

    const list =
        document.getElementById(
            "savedCodeList"
        );

    if (!list) return;

    const codes =
        await apiRequest(
            "/api/code/list/" +
            languageId
        );

    list.innerHTML = "";

    if (codes.length === 0) {

        list.innerHTML =
            "<p class='muted'>No saved code yet.</p>";

        return;

    }

    codes.forEach(
        function(code) {

            const item =
                document.createElement("div");

            item.className =
                "saved-code-item";

            item.innerHTML = `
                <strong>${code.title}</strong><br>
                <small>
                    📚 ${code.topic || "No topic"}<br>
                    📅 ${code.created_at}
                </small>
            `;

            item.addEventListener(
                "click",
                function() {

                    document
                        .getElementById(
                            "codeTitle"
                        )
                        .value =
                            code.title;

                    document
                        .getElementById(
                            "codeArea"
                        )
                        .value =
                            code.code;

                    document
                        .getElementById(
                            "codeTopic"
                        )
                        .value =
                            code.topic;

                }
            );

            list.appendChild(item);

        }
    );

}


/* =================================
   FLOW EDITOR
================================= */

let selectedTool = null;
let selectedShape = null;
let shapes = [];


function setupFlowEditor() {

    const canvas =
        document.getElementById(
            "flowCanvas"
        );

    if (!canvas) return;


    document
        .querySelectorAll(".shape-tool")
        .forEach(
            function(button) {

                button.addEventListener(
                    "click",
                    function() {

                        selectedTool =
                            button.dataset.shape;

                    }
                );

            }
        );


    canvas.addEventListener(
        "click",
        function(event) {

            if (
                event.target !== canvas
            ) return;

            if (!selectedTool) return;

            const rect =
                canvas.getBoundingClientRect();

            const x =
                event.clientX -
                rect.left;

            const y =
                event.clientY -
                rect.top;

            createShape(
                selectedTool,
                x,
                y,
                selectedTool
            );

        }
    );


    document
        .getElementById(
            "deleteSelectedTool"
        )
        .addEventListener(
            "click",
            function() {

                if (
                    selectedShape &&
                    selectedShape.element
                ) {

                    selectedShape.element.remove();

                    shapes =
                        shapes.filter(
                            s =>
                                s !== selectedShape
                        );

                    selectedShape = null;

                }

            }
        );


    document
        .getElementById(
            "clearCanvasTool"
        )
        .addEventListener(
            "click",
            function() {

                shapes = [];

                canvas.innerHTML =
                    `<div class="canvas-hint">
                        Select a tool and click on canvas.
                    </div>`;

            }
        );


    setupSaveFlow();

    loadSavedFlows();

}


function createShape(
    type,
    x,
    y,
    text
) {

    const canvas =
        document.getElementById(
            "flowCanvas"
        );

    const element =
        document.createElement("div");

    element.className =
        "flow-shape shape-" +
        type;

    const span =
        document.createElement("span");

    span.textContent = text;

    element.appendChild(span);

    element.style.left =
        x + "px";

    element.style.top =
        y + "px";

    canvas.appendChild(element);

    const shape = {
        type: type,
        x: x,
        y: y,
        text: text,
        element: element
    };

    shapes.push(shape);

    makeDraggable(
        element,
        shape
    );

    element.addEventListener(
        "click",
        function(event) {

            event.stopPropagation();

            document
                .querySelectorAll(
                    ".flow-shape"
                )
                .forEach(
                    el =>
                        el.classList.remove(
                            "selected"
                        )
                );

            element.classList.add(
                "selected"
            );

            selectedShape =
                shape;

        }
    );

}


function makeDraggable(
    element,
    shape
) {

    let offsetX = 0;
    let offsetY = 0;
    let dragging = false;


    element.addEventListener(
        "mousedown",
        function(event) {

            dragging = true;

            offsetX =
                event.clientX -
                element.offsetLeft;

            offsetY =
                event.clientY -
                element.offsetTop;

        }
    );


    document.addEventListener(
        "mousemove",
        function(event) {

            if (!dragging) return;

            const canvas =
                document.getElementById(
                    "flowCanvas"
                );

            const rect =
                canvas.getBoundingClientRect();

            let x =
                event.clientX -
                rect.left -
                offsetX;

            let y =
                event.clientY -
                rect.top -
                offsetY;

            x = Math.max(
                0,
                Math.min(
                    x,
                    canvas.clientWidth -
                    element.offsetWidth
                )
            );

            y = Math.max(
                0,
                Math.min(
                    y,
                    canvas.clientHeight -
                    element.offsetHeight
                )
            );

            element.style.left =
                x + "px";

            element.style.top =
                y + "px";

            shape.x = x;
            shape.y = y;

        }
    );


    document.addEventListener(
        "mouseup",
        function() {

            dragging = false;

        }
    );

}


function setupSaveFlow() {

    const button =
        document.getElementById(
            "saveFlowBtn"
        );

    if (!button) return;

    button.addEventListener(
        "click",
        async function() {

            const title =
                document
                    .getElementById(
                        "flowTitle"
                    )
                    .value
                    .trim() ||
                "My Flowchart";

            const cleanShapes =
                shapes.map(
                    function(shape) {

                        return {
                            type:
                                shape.type,

                            x:
                                shape.x,

                            y:
                                shape.y,

                            text:
                                shape.text
                        };

                    }
                );

            const result =
                await apiRequest(
                    "/api/flow/save",
                    "POST",
                    {
                        title:
                            title,

                        diagram_data:
                            JSON.stringify(
                                cleanShapes
                            )
                    }
                );

            const message =
                document.getElementById(
                    "flowMessage"
                );

            message.style.color =
                "#22c55e";

            message.textContent =
                result.message;

            loadSavedFlows();

        }
    );

}


async function loadSavedFlows() {

    const list =
        document.getElementById(
            "savedFlowList"
        );

    if (!list) return;

    const flows =
        await apiRequest("/api/flow");

    list.innerHTML = "";

    if (flows.length === 0) {

        list.innerHTML =
            "<p class='muted'>No flowchart saved yet.</p>";

        return;

    }

    flows.forEach(
        function(flow) {

            const item =
                document.createElement("div");

            item.className =
                "saved-flow-item";

            item.innerHTML = `
                <strong>${flow.title}</strong>
                <button onclick="loadFlowDiagram(${flow.id})">
                    Load
                </button>
            `;

            list.appendChild(item);

        }
    );

}


async function loadFlowDiagram(id) {

    const flows =
        await apiRequest("/api/flow");

    const flow =
        flows.find(
            item => item.id === id
        );

    if (!flow) return;

    document
        .getElementById(
            "flowTitle"
        )
        .value =
            flow.title;

    const canvas =
        document.getElementById(
            "flowCanvas"
        );

    canvas.innerHTML = "";

    shapes = [];

    const savedShapes =
        JSON.parse(
            flow.diagram_data
        );

    savedShapes.forEach(
        function(shape) {

            createShape(
                shape.type,
                shape.x,
                shape.y,
                shape.text
            );

        }
    );

}


/* =================================
   PAGE INITIALIZATION
================================= */

document.addEventListener(
    "DOMContentLoaded",
    function() {

        if (
            document.getElementById(
                "loginForm"
            )
        ) {

            setupLogin();

        }


        if (
            document.getElementById(
                "languageGrid"
            )
        ) {

            loadDashboard();

            loadHeatmap();

            loadLanguages();

            setupAddLanguage();

            startLiveClock();

        }


        if (
            document.getElementById(
                "workspaceTitle"
            )
        ) {

            loadWorkspace();

            setupTimer();

            setupSaveCode();

        }


        if (
            document.getElementById(
                "flowCanvas"
            )
        ) {

            setupFlowEditor();

        }

    }
);