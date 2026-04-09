document.addEventListener("DOMContentLoaded", function () {
  cargarDashboardCharts();
});


function cargarDashboardCharts() {
  fetch("/dashboards/api/charts/", {
    method: "GET",
    headers: {
      "X-Requested-With": "XMLHttpRequest",
    }
  })
    .then(response => {
      if (!response.ok) {
        throw new Error("Error en la respuesta del servidor");
      }
      return response.json();
    })
    .then(data => {
      if (data.error) {
        console.error("Error backend:", data.error);
        return;
      }

      carga_charts(data); // 👈 tu función existente
    })
    .catch(error => {
      console.error("Error cargando charts:", error);
    });
}


function carga_charts(Response) {
  const container = document.getElementById('dashboard-charts-container');
  container.innerHTML = '';

  const charts = Response.lista_charts || [];
  const valores = Response.valores_charts || {};

  if (charts.length === 0) {
    container.innerHTML = `
      <div class="col-12 text-center">
        <h5>No hay charts disponibles</h5>
      </div>
    `;
    return;
  }

  charts.forEach(chart => {
    const tipo = chart.TipoChart;
    const data = valores[chart.id] || [];

    if (tipo === 'Chart JS') {
      renderChartJS(container, chart, data);
    }

    if (tipo === 'Echarts') {
      renderEcharts(container, chart, data);
    }

    if (tipo === 'Tabla') {
      renderTabla(container, chart, data);
    }
  });
}

function renderChartJS(container, chart, data) {
  const div = document.createElement('div');
  div.className = chart.HtmlClass || 'col-md-6';

  const canvasId = 'chart_' + chart.id;

  div.innerHTML = `
    <div class="card shadow mb-4">
      <div class="card-header">
        <h6 class="m-0 font-weight-bold text-primary">${chart.Titulo}</h6>
      </div>
      <div class="card-body">
        <div style="height:250px;">
            <canvas id="${canvasId}"></canvas>
        </div>
      </div>
    </div>
  `;

  container.appendChild(div);

  const labels = data.map(row => row[chart.DatoX]);
  const values = data.map(row => parseFloat(row[chart.CampoValor]));

  let type = 'bar';

  if (chart.ModeloChart === 'Barras') type = 'line';
  if (chart.ModeloChart === 'Pastel') type = 'pie';

  new Chart(document.getElementById(canvasId), {
    type: type,
    data: {
      labels: labels,
      datasets: [{
        label: chart.Label || chart.Titulo,
        data: values,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false
    }
  });
}


function renderEcharts(container, chart, data) {
  const div = document.createElement('div');
  div.className = chart.HtmlClass || 'col-md-3';

  const id = 'chart_' + chart.id;
  div.innerHTML = `<div id="${id}"></div>`;
  container.appendChild(div);

  const dom = document.getElementById(id);

  if (!data || !data.length) return;

  if (chart.ModeloChart === 'Gauge') {

    let lis_valor = chart.DatoX.split(',');
    let lis_meta = chart.NombreDatoX.split(',');

    // Normalización (IMPORTANTE)
    if (lis_valor.length === 1) {
      lis_valor = [chart.DatoX, chart.DatoX];
    }
    if (lis_meta.length === 1) {
      lis_meta = [chart.NombreDatoX, chart.NombreDatoX];
    }

    let row = data[0];

    let ch_valor = 0;
    let ch_display = 0;
    let ch_meta = 0;
    let ch_meta_display = 0;
    let ch_base = 0;

    // Validación valor
    if (isNaN(row[lis_valor[0]])) {
      ch_valor = 0;
      ch_display = 0;
    } else {
      ch_valor = row[lis_valor[0]];
      ch_display = row[lis_valor[1]];
    }

    // Meta
    ch_meta = row[lis_meta[0]];
    ch_meta_display = row[lis_meta[1]];

    // Base
    ch_base = row[chart.NombreDatoY];

    // Null safety (IGUAL QUE ORIGINAL)
    if (ch_meta == null) {
      ch_meta = 0;
      ch_meta_display = 0;
    }

    if (ch_base == null) ch_base = 0;

    if (ch_valor == null) {
      ch_valor = 0;
      ch_display = 0;
    }

    let color = 'green';
    let porcentaje = 0;

    // 🔴 CASO META = 0 (usa base)
    if (parseInt(ch_meta) === 0) {

      let calc = parseInt(parseFloat(ch_valor / ch_base) * 100);

      if (calc <= 33) color = 'green';
      if (calc > 33 && calc <= 66) color = 'yellow';
      if (calc > 66) color = 'red';

      // ⚠️ IMPORTANTE: el original usa ch_meta aquí (aunque sea 0)
      porcentaje = parseInt(parseFloat(ch_valor / ch_meta) * 100);

    } else {

      let calc = parseInt(parseFloat(ch_valor / ch_meta) * 100);

      if (calc <= 33) color = 'red';
      if (calc > 33 && calc <= 66) color = 'yellow';
      if (calc > 66) color = 'green';

      porcentaje = calc;
    }

    dom.innerHTML = `
      <div class="info-box bg-${color}">
        <span class="info-box-icon">
          <i class="fa fa-fw fa-tachometer-alt"></i>
        </span>
        <div class="info-box-content">
          <span class="info-box-text">${chart.Titulo}</span>
          <span class="info-box-number">${ch_display}</span>
          <div class="progress">
            <div class="progress-bar" style="width: ${porcentaje}%"></div>
          </div>
          <span class="progress-description">${ch_meta_display}</span>
        </div>
      </div>
    `;
  }

  if (chart.ModeloChart === 'Gauge2') {

    let lis_valor = chart.DatoX.split(',');
    let lis_meta = chart.NombreDatoX.split(',');

    let row = data[0];

    let ch_valor = 0;
    let ch_display = 0;

    if (isNaN(row[lis_valor[0]])) {
      ch_valor = 0;
      ch_display = 0;
    } else {
      ch_valor = row[lis_valor[0]];
      ch_display = row[lis_valor[1]];
    }

    let ch_barra = 0;
    let color = 'green';
    let ch_meta_display = 0;

    if (lis_meta[0] === 'Negativo') {

      ch_meta_display = lis_meta[1];

      if (parseFloat(ch_valor) >= parseFloat(lis_meta[1])) {
        color = 'green';
        ch_barra = 100;
      }
      if (parseFloat(ch_valor) >= parseFloat(lis_meta[2])) {
        color = 'yellow';
        ch_barra = 50;
      }
      if (parseFloat(ch_valor) >= parseFloat(lis_meta[3])) {
        color = 'red';
        ch_barra = 10;
      }
    }

    if (lis_meta[0] === 'Positivo') {

      ch_meta_display = lis_meta[3];
      color = 'red';

      if (parseFloat(ch_valor) >= parseFloat(lis_meta[1])) {
        color = 'red';
        ch_barra = 10;
      }
      if (parseFloat(ch_valor) >= parseFloat(lis_meta[2])) {
        color = 'yellow';
        ch_barra = 50;
      }
      if (parseFloat(ch_valor) >= parseFloat(lis_meta[3])) {
        color = 'green';
        ch_barra = 100;
      }
    }

    dom.innerHTML = `
      <div class="info-box bg-${color}">
        <span class="info-box-icon">
          <i class="fa fa-fw fa-tachometer-alt"></i>
        </span>
        <div class="info-box-content">
          <span class="info-box-text">${chart.Titulo}</span>
          <span class="info-box-number">${ch_display}</span>
          <div class="progress">
            <div class="progress-bar" style="width: ${ch_barra}%"></div>
          </div>
          <span class="progress-description">${ch_meta_display}</span>
        </div>
      </div>
    `;
  }
}


function renderTabla(container, chart, data) {
  const div = document.createElement('div');
  div.className = chart.HtmlClass || 'col-md-12';

  const columnas = chart.DatoX.split(',');

  let html = `
    <div class="card shadow mb-4">
      <div class="card-header">
        <h6 class="m-0 font-weight-bold text-primary">${chart.Titulo}</h6>
      </div>
      <div class="card-body">
        <div style="overflow-x:auto;">
        <table class="table table-bordered">
          <thead>
            <tr>
  `;

  columnas.forEach(col => {
    html += `<th>${col}</th>`;
  });

  html += `</tr></thead><tbody>`;

  data.forEach(row => {
    html += '<tr>';
    columnas.forEach(col => {
      html += `<td>${row[col] ?? ''}</td>`;
    });
    html += '</tr>';
  });

  html += `
          </tbody>
        </table>
        </div>
      </div>
    </div>
  `;

  div.innerHTML = html;
  container.appendChild(div);
}
