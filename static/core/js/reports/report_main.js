var report_data = {
    meta: {},
    parametros: {},
    niveles_config: [],
    exportacion_config: {},
    resultado_niveles: {}
};

$(document).ready(function () {

    initializeReportData();

    $("#btn-execute-report").on("click", function () {
        executeLevel(0);
    });

    $(document).on("click", "#btn-export-excel", function () {
        exportToExcel();
    });

    $(document).on("click", "#btn-export-pdf", function () {
        exportToPdf();
    });
    $(document).on("change", "#chk-export-subniveles", function () {

        const isChecked = $(this).is(":checked");

        const text = isChecked
            ? "Exportar con detalle"
            : "Exportar sin detalle";

        $("#switch-label-text").text(text);

    });

});


function initializeReportData() {

    const parsed = JSON.parse(
        document.getElementById("report-data").textContent
    );

    report_data.meta = {
        id: parsed.id,
        nombre: parsed.nombre,
        descripcion: parsed.descripcion
    };

    report_data.parametros = parsed.parametros;
    report_data.niveles_config = parsed.niveles;
    report_data.exportacion_config = parsed.exportable;
}


function collectParametros() {

    const parametros = {};

    $(".report-variable").each(function () {
        parametros[$(this).data("key")] = $(this).val();
    });

    $(".report-reference").each(function () {
        parametros[$(this).data("key")] = $(this).val();
    });

    return parametros;
}


function executeLevel(nivel) {

    $.ajax({
        url: `/reports/api/execute/${report_data.meta.id}/`,
        method: "POST",
        headers: {
            "X-CSRFToken": getCSRFToken(),
        },
        contentType: "application/json",
        data: JSON.stringify({
            nivel: nivel,
            parametros: collectParametros()
        }),
        success: function (response) {

            report_data.resultado_niveles[nivel] = response.data;

            if (nivel === 0) {
                renderNivel(0, null);
            }

            if (report_data.niveles_config.length > nivel + 1) {
                setTimeout(() => {
                    executeLevel(nivel + 1);
                }, 0);
            }
        },
        error: function () {
            renderError("Error ejecutando nivel " + nivel);
        }
    });
}

function renderNivel(nivel, parentKey) {

    if (nivel === 0) {
        renderMainTable();
    }
}

function renderMainTable() {

    const container = $("#report-results");
    container.empty();

    const nivelConfig = report_data.niveles_config[0];
    const columnas = nivelConfig.columnas;
    const campoHijo = nivelConfig.vinculos?.campo_hijo;

    const hasNextNivel = report_data.niveles_config.length > 1 && campoHijo;

    const rows = report_data.resultado_niveles[0] || [];

    if (!rows.length) {
        container.html(`<div class="alert alert-warning">Sin registros.</div>`);
        return;
    }

    let html = `
        <div class="card shadow mb-4">

            <div class="card-header py-3 d-flex justify-content-between align-items-start">
    
                <h5 class="m-0 font-weight-bold text-primary">
                    Reporte: ${report_data.meta.nombre}
                </h5>

                <div class="d-flex align-items-center">
                <!-- Botones -->
                    <div class="d-flex"> 
                        <button id="btn-export-excel" class="btn btn-sm btn-success mr-2" style="padding: 10px 20px;font-weight: bold;font-size: 15px;"> 
                            <i class="fas fa-file-excel"></i> 
                                Generar Excel 
                        </button> 
                        <button id="btn-export-pdf" class="btn btn-sm btn-danger" style="padding: 10px 20px;font-weight: bold;font-size: 15px;"> 
                            <i class="fas fa-file-pdf"></i> 
                            Generar PDF 
                        </button> 
                    </div>
                    <!-- Switch + iconos -->
                    <div class="d-flex flex-column align-items-center mr-4" style="margin-left: 20px;">
                        <div class="d-flex align-items-center">
                            <img src="${STATIC_ICONS.sin}"
                                width="35"
                                class="icon-sin"
                                title="Sin subniveles">

                            <div class="custom-control custom-switch custom-switch-lg mx-2">
                                <input type="checkbox"
                                    class="custom-control-input"
                                    id="chk-export-subniveles">

                                <label class="custom-control-label"
                                    for="chk-export-subniveles">
                                </label>
                            </div>

                            <img src="${STATIC_ICONS.con}"
                                width="35"
                                class="icon-con"
                                title="Con subniveles">

                        </div>

                        <small id="switch-label-text"
                            class="mt-1 font-weight-bold text-muted">
                            Exportar sin detalle
                        </small>

                    </div>

                </div>

            </div>

            <div class="card-body">

                <!-- Barra de carga exportación -->
                <div id="export-loader-container" class="mb-3" style="display:none;">

                    <div class="d-flex justify-content-between">
                        <small id="export-loader-text">Preparando exportación...</small>
                        <small><span id="export-loader-percent">0</span>%</small>
                    </div>

                    <div class="progress" style="height: 8px;">
                        <div id="export-loader-bar"
                            class="progress-bar progress-bar-striped progress-bar-animated bg-success"
                            role="progressbar"
                            style="width: 0%">
                        </div>
                    </div>
                </div>

                <div class="table-responsive">
                    <table class="table table-bordered table-sm"
                           id="reportTable"
                           width="100%">
                        <thead>
                            <tr>
                                <th style="width:60px;"></th>
    `;

    columnas.forEach(col => {
        html += `<th>${col}</th>`;
    });

    html += `
                            </tr>
                        </thead>
                        <tbody>
    `;

    rows.forEach(row => {

        let keyAttr = "";
        let expandBtn = "";

        if (hasNextNivel) {

            const key = row[campoHijo];

            keyAttr = `data-key="${key}" data-nivel="0" data-isloaded="false"`;

            expandBtn = `<button class="btn btn-sm btn-primary btn-expand">+</button>`;

        } else {

            keyAttr = `data-nivel="0"`;
            expandBtn = "";

        }

        html += `<tr ${keyAttr}>`;

        html += `
            <td class="text-center">
                ${expandBtn}
            </td>
        `;

        columnas.forEach(col => {
            html += `<td>${row[col] ?? ""}</td>`;
        });

        html += `</tr>`;
    });

    const totalesConfig = nivelConfig.totales || [];
    const totalesCalculados = calcularTotales(rows, totalesConfig);

    html += `</tbody>`;

    if (totalesConfig.length) {

        html += `<tfoot><tr><th></th>`;

        columnas.forEach(col => {

            if (totalesCalculados[col] !== undefined) {
                html += `<th>${totalesCalculados[col].toFixed(2)}</th>`;
            } else {
                html += `<th></th>`;
            }

        });

        html += `</tr></tfoot>`;
    }

    html += `
                    </table>
                </div>
            </div>
        </div>
    `;

    container.html(html);

    initializeReportDataTable();
}


let reportDataTable = null;

function initializeReportDataTable(columns) {

    if ($.fn.DataTable.isDataTable('#reportTable')) {
        $('#reportTable').DataTable().destroy();
    }

    reportDataTable = $('#reportTable').DataTable({
        pageLength: 10,
        lengthChange: false,
        searching: false,
        ordering: true,
        info: true,
        responsive: true,
        language: {
            paginate: {
                previous: "Anterior",
                next: "Siguiente"
            },
            info: "Mostrando _START_ a _END_ de _TOTAL_ registros",
            infoEmpty: "Sin registros disponibles",
            zeroRecords: "No se encontraron resultados"
        }
    });

    attachExpandEvents(columns);
}

function attachExpandEvents() {

    $(document)
        .off('click', '#report-results button.btn-expand')
        .on('click', '#report-results button.btn-expand', function () {
            const tr = $(this).closest('tr');

            const nivel = parseInt(tr.data('nivel'));
            const key = tr.data('key');
            const isLoaded = tr.data('isloaded');
            const nextNivel = nivel + 1;

            // =====================================
            // ===== NIVEL 0 (DataTable) ===========
            // =====================================
            if (nivel === 0) {

                const row = reportDataTable.row(tr);

                if (row.child.isShown()) {
                    row.child.hide();
                    $(this).text('+');
                    return;
                }

                if (!isLoaded) {

                    const subHtml = buildSubNivelHtml(nextNivel, key);

                    row.child(subHtml).show();

                    tr.data('isloaded', true);

                } else {
                    row.child.show();
                }

            }
            // =====================================
            // ===== NIVELES > 0 ===================
            // =====================================
            else {

                const existingChild = tr.next('.subnivel-row');

                if (existingChild.length) {
                    existingChild.remove();
                    $(this).text('+');
                    return;
                }

                if (!isLoaded) {

                    const subHtml = buildSubNivelHtml(nextNivel, key);

                    tr.after(`
                        <tr class="subnivel-row">
                            <td colspan="${tr.children('td').length}">
                                ${subHtml}
                            </td>
                        </tr>
                    `);

                    tr.data('isloaded', true);

                } else {

                    tr.after(`
                        <tr class="subnivel-row">
                            <td colspan="${tr.children('td').length}">
                                ${buildSubNivelHtml(nextNivel, key)}
                            </td>
                        </tr>
                    `);
                }
            }

            $(this).text('-');
        });
}

function buildSubNivelHtml(nivel, parentKey) {

    try {
        const nivelConfig = report_data.niveles_config[nivel];

        if (!nivelConfig) {
            return `<div class="p-2 text-muted">Sin nivel</div>`;
        }

        const columnas = nivelConfig.columnas;
        const campoPadre = nivelConfig.vinculos?.campo_padre;
        const campoHijo = nivelConfig.vinculos?.campo_hijo;

        const hasNextNivel = report_data.niveles_config.length > nivel + 1 && campoHijo;

        const grouped = report_data.resultado_niveles[nivel] || {};
        const rows = grouped[String(parentKey)] || [];

        if (!rows.length) {
            return `<div class="p-2 text-muted">Sin detalle</div>`;
        }

        let html = `<table class="table table-sm table-bordered mb-0">
                        <thead>
                            <tr>
                                <th style="width:60px;"></th>`;

        columnas.forEach(col => {
            html += `<th>${col}</th>`;
        });

        html += `</tr></thead><tbody>`;

        rows.forEach(row => {

            let keyAttr = "";
            let expandBtn = "";

            if (hasNextNivel) {

                const key = row[campoHijo];

                keyAttr = `data-key="${key}" data-nivel="${nivel}" data-isloaded="false"`;

                expandBtn = `<button class="btn btn-sm btn-primary btn-expand">+</button>`;

            } else {

                keyAttr = `data-nivel="${nivel}"`;
                expandBtn = "";

            }

            html += `<tr ${keyAttr}>`;

            html += `
                <td class="text-center">
                    ${expandBtn}
                </td>
            `;

            columnas.forEach(col => {
                html += `<td>${row[col] ?? ""}</td>`;
            });

            html += `</tr>`;
        });

        const totalesConfig = nivelConfig.totales || [];
        const totalesCalculados = calcularTotales(rows, totalesConfig);

        html += `</tbody>`;

        if (totalesConfig.length) {

            html += `<tfoot><tr><th></th>`;

            columnas.forEach(col => {
                if (totalesCalculados[col] !== undefined) {
                    html += `<th>${totalesCalculados[col].toFixed(2)}</th>`;
                } else {
                    html += `<th></th>`;
                }
            });

            html += `</tr></tfoot>`;
        }

        html += `</table>`;

        return html;

    } catch (error) {

        console.error("Error building subnivel HTML:", error);

        return `<div class="p-2 text-danger">Error al cargar detalle</div>`;
    }
}

function calcularTotales(rows, totalesConfig) {

    if (!totalesConfig || !totalesConfig.length) return {};

    const resultado = {};

    totalesConfig.forEach(total => {
        if (total.tipo === "SUM") {

            resultado[total.columna] = rows.reduce((acc, row) => {
                const valor = parseFloat(row[total.columna]);
                return acc + (isNaN(valor) ? 0 : valor);
            }, 0);
        }
    });

    return resultado;
}




function renderError(message) {

    $("#report-results").html(`
        <div class="alert alert-danger">${message}</div>
    `);
}

// ===============================
// EXPORT LOADER CONTROL
// ===============================

function showLoader(text = "Procesando...") {

    $("#export-loader-text").text(text);
    $("#export-loader-percent").text(0);
    $("#export-loader-bar").css("width", "0%");
    $("#export-loader-container").show();
}

function updateLoader(percent, text = null) {

    if (text) {
        $("#export-loader-text").text(text);
    }

    $("#export-loader-percent").text(percent);
    $("#export-loader-bar").css("width", percent + "%");
}

function hideLoader() {

    setTimeout(() => {
        $("#export-loader-container").fadeOut();
    }, 400);
}

// ===============================
// EXPORT FUNCTIONS
// ===============================

async function exportToExcel() {

    const incluirSubniveles = $("#chk-export-subniveles").is(":checked");

    showLoader("Generando Excel...");

    const reporte = report_data;

    try {

        await generateExcelReport(reporte, incluirSubniveles);

    } catch (error) {

        console.error("Error generando Excel:", error);
        alert("Error generando Excel.");

    } finally {

        hideLoader();
    }
}

async function exportToPdf() {
    const incluirSubniveles = $("#chk-export-subniveles").is(":checked");

    showLoader("Generando PDF...");

    const reporte = report_data;

    try {

        await generatePdfReport(reporte, incluirSubniveles);

    } catch (error) {

        console.error("Error generando PDF:", error);
        alert("Error generando PDF.");

    } finally {

        hideLoader();
    }
}

//^ función temporal de simulación
function simulateProgress() {
    return new Promise(resolve => {
        let progress = 0;
        const interval = setInterval(() => {
            progress += 10;
            updateLoader(progress);
            if (progress >= 100) {
                clearInterval(interval);
                resolve();
            }
        }, 120);
    });
}