document.addEventListener("DOMContentLoaded", () => {
    const configsTableBody = document.getElementById("configs-table-body");

    async function fetchConfigs() {
        try {
            const response = await fetch("/api/v1/configurations");
            const configs = await response.json();
            renderConfigs(configs);
        } catch (error) {
            console.error("Error fetching configurations:", error);
        }
    }

    function renderConfigs(configs) {
        configsTableBody.innerHTML = "";
        configs.forEach(config => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td>${config.protocol}</td>
                <td>${config.server}</td>
                <td>${config.port}</td>
                <td><button class="edit-btn" data-id="${config.id}">Edit</button></td>
            `;
            configsTableBody.appendChild(row);
        });

        document.querySelectorAll(".edit-btn").forEach(btn => {
            btn.addEventListener("click", handleEditClick);
        });
    }

    function handleEditClick(event) {
        const configId = event.target.dataset.id;
        // Fetch the full config details from the API
        // For now, we'll just populate the modal with dummy data
        document.getElementById("edit-id").value = configId;
        document.getElementById("edit-protocol").value = "vmess";
        document.getElementById("edit-server").value = "test.server.com";
        document.getElementById("edit-port").value = 443;
        document.getElementById("edit-modal").style.display = "block";
    }

    const modal = document.getElementById("edit-modal");
    const closeBtn = document.querySelector(".close-btn");
    closeBtn.addEventListener("click", () => {
        modal.style.display = "none";
    });

    window.addEventListener("click", event => {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    });

    fetchConfigs();
});
