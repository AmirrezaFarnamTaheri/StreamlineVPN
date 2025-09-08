document.addEventListener("DOMContentLoaded", function() {
    fetch('/_includes/header.html')
        .then(response => response.text())
        .then(data => {
            document.body.insertAdjacentHTML('afterbegin', data);
        });
});
