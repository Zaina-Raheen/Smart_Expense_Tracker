(function () {
  var desc = document.getElementById('id_description');
  var category = document.getElementById('id_category');
  var hint = document.getElementById('suggestion');
  if (!desc || !category || !hint) return;

  var timer = null;

  function update() {
    var text = desc.value.trim();
    if (!text) { hint.textContent = ''; return; }
    fetch(window.PREDICT_URL + '?description=' + encodeURIComponent(text))
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (category.value === '') {
          hint.textContent = 'Will be saved as: ' + data.category;
        } else {
          hint.textContent = 'Suggested category: ' + data.category;
        }
      })
      .catch(function () { hint.textContent = ''; });
  }

  desc.addEventListener('input', function () {
    clearTimeout(timer);
    timer = setTimeout(update, 250);
  });
  category.addEventListener('change', update);
  update();
})();
