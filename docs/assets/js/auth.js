document.addEventListener("DOMContentLoaded", () => {
    const accessToken = localStorage.getItem("access_token");
    if (!accessToken) {
        window.location.href = "login.html";
    }
});
