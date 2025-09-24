document.addEventListener("DOMContentLoaded", () => {
    const logContainer = document.getElementById("log-container");
    const ws = new WebSocket(`ws://${window.location.host}/api/v1/ws/logs`);

    ws.onmessage = event => {
        const logEntry = document.createElement("div");
        logEntry.textContent = event.data;
        logContainer.appendChild(logEntry);
        logContainer.scrollTop = logContainer.scrollHeight;
    };

    ws.onopen = () => {
        console.log("WebSocket connection opened.");
    };

    ws.onerror = error => {
        console.error("WebSocket error:", error);
    };

    ws.onclose = () => {
        console.log("WebSocket connection closed.");
    };
});
