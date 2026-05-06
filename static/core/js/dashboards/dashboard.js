document.addEventListener("DOMContentLoaded", function () {

  if (!window.APP || !window.APP.hasModules) {
    return;
  }

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
    const modelo = (chart.modeloChart || '').toLowerCase();
    const data = valores[chart.id] || [];

    // Chart.js
    if (['torres', 'barras', 'pastel'].includes(modelo)) {
      renderChartJS(container, chart, data);
      return;
    }

    // Echarts / Gauge visuales
    if (['gauge', 'gauge2'].includes(modelo)) {
      renderEcharts(container, chart, data);
      return;
    }

    // Tabla
    if (modelo === 'tabla') {
      renderTabla(container, chart, data);
      return;
    }

    // Calendario
    if (modelo === 'calendario') {
      renderCalendario(container, chart, data);
      return;
    }

    console.warn(`Modelo de chart no soportado: ${chart.modeloChart}`);
  });
}

function renderChartJS(container, chart, data) {
  const div = document.createElement('div');
  div.className = chart.htmlClass || 'col-md-6';

  const canvasId = 'chart_' + chart.id;
  const config = chart.configuracion || {};

  div.innerHTML = `
    <div class="card shadow mb-4">
      <div class="card-header">
        <h6 class="m-0 font-weight-bold text-primary">${chart.titulo}</h6>
      </div>
      <div class="card-body">
        <div style="height:250px;">
          <canvas id="${canvasId}"></canvas>
        </div>
      </div>
    </div>
  `;

  container.appendChild(div);

  const labels = data.map(row => row[config.datoX]);
  const values = data.map(row => parseFloat(row[config.campoValor]));

  let type = 'bar';
  const modelo = (chart.modeloChart || '').toLowerCase();

  if (modelo === 'barras') type = 'line';
  if (modelo === 'pastel') type = 'pie';

  new Chart(document.getElementById(canvasId), {
    type: type,
    data: {
      labels: labels,
      datasets: [{
        label: chart.label || chart.titulo,
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
  div.className = chart.htmlClass || 'col-md-3';

  const id = 'chart_' + chart.id;
  div.innerHTML = `<div id="${id}"></div>`;
  container.appendChild(div);

  const dom = document.getElementById(id);
  const config = chart.configuracion || {};
  const modelo = (chart.modeloChart || '').toLowerCase();

  if (!data || !data.length) return;

  /*
  =====================================================
  GAUGE
  =====================================================
  */
  if (modelo === 'gauge') {

    let lis_valor = (config.datoX || '').split(',');
    let lis_meta = (config.nombreDatoX || '').split(',');

    // Normalización original
    if (lis_valor.length === 1) {
      lis_valor = [config.datoX, config.datoX];
    }

    if (lis_meta.length === 1) {
      lis_meta = [config.nombreDatoX, config.nombreDatoX];
    }

    const row = data[0];

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
    ch_base = row[config.nombreDatoY];

    // Null safety original
    if (ch_meta == null) {
      ch_meta = 0;
      ch_meta_display = 0;
    }

    if (ch_base == null) {
      ch_base = 0;
    }

    if (ch_valor == null) {
      ch_valor = 0;
      ch_display = 0;
    }

    let color = 'green';
    let porcentaje = 0;

    /*
    IMPORTANTE:
    Se mantiene exactamente la lógica original,
    incluso el comportamiento raro de dividir entre ch_meta = 0
    porque así estaba implementado.
    */

    if (parseInt(ch_meta) === 0) {

      let calc = parseInt(parseFloat(ch_valor / ch_base) * 100);

      if (calc <= 33) color = 'green';
      if (calc > 33 && calc <= 66) color = 'yellow';
      if (calc > 66) color = 'red';

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
          <span class="info-box-text">${chart.titulo}</span>
          <span class="info-box-number">${ch_display}</span>

          <div class="progress">
            <div class="progress-bar" style="width: ${porcentaje}%"></div>
          </div>

          <span class="progress-description">
            ${ch_meta_display}
          </span>
        </div>
      </div>
    `;

    return;
  }

  /*
  =====================================================
  GAUGE 2
  =====================================================
  */
  if (modelo === 'gauge2') {

    let lis_valor = (config.datoX || '').split(',');
    let lis_meta = (config.nombreDatoX || '').split(',');

    const row = data[0];

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
          <span class="info-box-text">${chart.titulo}</span>
          <span class="info-box-number">${ch_display}</span>

          <div class="progress">
            <div class="progress-bar" style="width: ${ch_barra}%"></div>
          </div>

          <span class="progress-description">
            ${ch_meta_display}
          </span>
        </div>
      </div>
    `;

    return;
  }
}


function renderTabla(container, chart, data) {
  const div = document.createElement('div');
  div.className = chart.htmlClass || 'col-md-12';

  const config = chart.configuracion || {};
  const columnas = (config.datoX || '').split(',');

  let html = `
    <div class="card shadow mb-4">
      <div class="card-header">
        <h6 class="m-0 font-weight-bold text-primary">
          ${chart.titulo}
        </h6>
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

  html += `
              </tr>
            </thead>
            <tbody>
  `;

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


function renderCalendario(container, chart, data) {
  const div = document.createElement('div');
  div.className = chart.htmlClass || 'col-md-12';

  const calendarId = 'calendar_' + chart.id;
  const config = chart.configuracion || {};

  div.innerHTML = `
    <div class="card shadow mb-4">
      <div class="card-header">
        <h6 class="m-0 font-weight-bold text-primary">
          ${chart.titulo}
        </h6>
      </div>

      <div class="card-body">
        <div id="${calendarId}"></div>
      </div>
    </div>
  `;

  container.appendChild(div);

  const calendarEl = document.getElementById(calendarId);

  if (!calendarEl) return;

  // =====================================================
  //  Construcción de eventos
  // =====================================================
  const events = data.map(row => {
    const titulo = row[config.campoTitulo] || 'Sin título';
    const fecha = row[config.campoFecha];
    const recordId = row[config.campoId];
    const modulo = row[config.campoModulo];

    // URL generada: /module/{modulo}/view/{id}/
    let url = '#';
    if (modulo && recordId) {
      url = `/module/${modulo}/view/${recordId}/`;
    }

    return {
      title: titulo,
      start: fecha,
      url: url,

      extendedProps: {
        modulo: modulo,
        recordId: recordId
      }
    };
  });

  // =====================================================
  //  Inicialización del calendario
  // =====================================================
  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: 'dayGridMonth',
    locale: 'es',
    height: 'auto',
    headerToolbar: {
      left: 'prev,next today',
      center: 'title',
      right: 'dayGridMonth,timeGridWeek,timeGridDay'
    },

    events: events,

    // Abrir en nueva pestaña
    eventClick: function (info) {
      info.jsEvent.preventDefault();

      if (info.event.url && info.event.url !== '#') {
        window.open(info.event.url, '_blank');
      }
    }
  });

  calendar.render();
}


//* Función para visualizar modal de plantillas desde el dashboard
function mostrarModalPlantillas() {
    // Cargar contenido del carrusel de plantillas
  let templateCarouselContainer = document.getElementById('templateCarouselContainer');
  templateCarouselContainer.innerHTML = `
  <div class="text-center">
  <div class="spinner-border text-primary" role="status">
  <span class="sr-only">Cargando...</span>
  </div>
  <p>Cargando plantillas...</p>
  </div>
  `;
  
  $('#templateCarouselModal').modal('show');

  fetch("/dashboards/api/modelos-prehechos/")
    .then(res => res.json())
    .then(data => {
      renderCarruselPlantillas(data.modelos);
    })
    .catch(err => {
      container.innerHTML = `<p class="text-danger">Error cargando plantillas</p>`;
      console.error(err);
    });
}

function renderCarruselPlantillas(modelos) {
  const container = document.getElementById('templateCarouselContainer');

  if (!modelos.length) {
    container.innerHTML = `<p class="text-center">No hay plantillas disponibles</p>`;
    return;
  }

  let items = modelos.map(m => {
    return `
      <div class="template-card">

        <div class="template-icon">
          ${renderIcono(m.icono)}
        </div>

        <div class="template-content">
          <h6 class="template-title">${m.nombre}</h6>
          <p class="template-desc">
            ${m.descripcion || ''}
          </p>
        </div>

        <button class="btn btn-primary btn-sm w-100 mt-auto"
          onclick="aplicarModelo(${m.id})">
          Usar
        </button>

      </div>
    `;
  }).join('');

  container.innerHTML = `
    <div class="templates-scroll-container">
      ${items}
    </div>
  `;
}

function renderIcono(icono) {
  if (!icono) return "📦";

  // =========================
  // IMAGEN (simplificado)
  // =========================
  if (icono.startsWith("img:")) {
    const fileName = icono.replace("img:", "");

    return `
      <img 
        src="/static/core/img/modelos_prehechos/${fileName}" 
        style="width:64px;height:64px;object-fit:contain;"
      />
    `;
  }

  // =========================
  // ICONO CSS
  // =========================
  if (icono.includes("bi ") || icono.includes("fa ")) {
    return `<i class="${icono}"></i>`;
  }

  // =========================
  // EMOJI
  // =========================
  return icono;
}


function aplicarModelo(id) {
  alert("Aplicar modelo ID: " + id);

  // luego aquí:
  // POST → backend → ejecutar jsons → sync → mysql
}


