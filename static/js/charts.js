(function () {
  var el = document.getElementById('chart-data');
  if (!el || typeof Chart === 'undefined') return;
  var data = JSON.parse(el.textContent);

  var colors = ['#1f4e79', '#c0622f', '#3d8361', '#8a5a9e', '#b8923a', '#4d93b5', '#a8453f', '#6b7280'];

  var catCanvas = document.getElementById('categoryChart');
  if (catCanvas) {
    new Chart(catCanvas, {
      type: 'pie',
      data: {
        labels: data.categories,
        datasets: [{ data: data.category_totals, backgroundColor: colors, borderColor: '#fff', borderWidth: 1 }]
      },
      options: {
        maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom' } }
      }
    });
  }

  var timeCanvas = document.getElementById('timeChart');
  if (timeCanvas) {
    new Chart(timeCanvas, {
      type: 'bar',
      data: {
        labels: data.dates,
        datasets: [{ label: 'Spent (Rs.)', data: data.date_totals, backgroundColor: '#1f4e79' }]
      },
      options: {
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true } }
      }
    });
  }
})();
