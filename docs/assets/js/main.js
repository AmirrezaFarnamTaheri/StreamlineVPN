document.addEventListener("DOMContentLoaded", function() {
  fetch('_includes/header.html')
    .then(response => {
      if (!response.ok) throw new Error(`Header load failed: ${response.status}`);
      return response.text();
    })
    .then(data => {
      document.body.insertAdjacentHTML('afterbegin', data);
    })
    .catch(err => console.warn(err));
});
