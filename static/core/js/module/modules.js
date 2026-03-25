function createModule() {
    const nameInput = document.getElementById("moduleNameInput");
    const descriptionInput = document.getElementById("moduleDescriptionInput");
    const usageInput = document.getElementById("moduleUsageInput");

    if (!nameInput || !descriptionInput || !usageInput) {
        alert("Error interno: inputs del módulo no encontrados");
        return;
    }

    const nombre = nameInput.value.trim();
    const descripcion = descriptionInput.value.trim();
    const uso = usageInput.value;

    if (!nombre) {
        alert("El nombre del módulo es obligatorio");
        return;
    }

    fetch("/module/create/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken(),
        },
        body: JSON.stringify({
            nombre: nombre,
            descripcion: descripcion,
            uso: uso,
        }),
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert("Módulo creado correctamente");
                window.location.reload();
            } else {
                alert(data.error || "Error al crear el módulo");
            }
        })
        .catch(error => {
            console.error("Error creando módulo:", error);
            alert("Error de comunicación con el servidor");
        });
}

function syncModuleSchema(moduleId) {

    if (!moduleId) {
        alert("ID del módulo no válido");
        return;
    }

    if (!confirm("¿Deseas sincronizar la estructura MySQL con MongoDB?")) {
        return;
    }

    fetch(`/module/${moduleId}/sync-schema/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken(),
        },
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert("Esquema sincronizado correctamente");
            } else {
                alert(data.error || "Error al sincronizar");
            }
        })
        .catch(error => {
            console.error("Error sincronizando esquema:", error);
            alert("Error de comunicación con el servidor");
        });
}


/* ============================================================
   DataTable Initialization
   ============================================================ */

let moduleDataTable = null;
let filtrosActivos = [];
let dictColumnasFiltro = {}; // indiceReal -> nombreColumna

document.addEventListener("DOMContentLoaded", function () {
    // =========================
    // Auto cerrar alertas
    // =========================
    const alert = document.getElementById("moduleAlert");
    if (alert) {
        setTimeout(() => {
            alert.classList.remove("show");

            setTimeout(() => {
                alert.remove();
            }, 300);

        }, 2500);
    }

    if (typeof $ === "undefined" || !$.fn.DataTable) {
        console.warn("DataTables no está cargado.");
        return;
    }

    const table = $('#moduleTable');

    if (!table.length) {
        return;
    }

    moduleDataTable = table.DataTable({
        pageLength: 10,
        lengthChange: false,
        ordering: true,
        searching: true,
        dom: 'lrtip',   // Se quita la "f" y la "p"
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
    // Mover info y paginación fuera del scroll
    setTimeout(function () {

        const wrapper = $('#moduleTable').closest('.dataTables_wrapper');

        const info = wrapper.find('.dataTables_info');
        const paginate = wrapper.find('.dataTables_paginate');

        $('#moduleTableInfo').append(info);
        $('#moduleTablePagination').append(paginate);

    }, 0);
    // Construir diccionario columnaNombre -> índiceReal
    dictColumnasFiltro = { "Todas": "Todas" };
    moduleDataTable.columns().every(function (index) {
        let header = $(this.header()).text().trim();
        if (header.toLowerCase() === "acciones") {
            return;
        }
        dictColumnasFiltro[index - 1] = header;
    });

    $.fn.dataTable.ext.search.push(function (settings, data, dataIndex) {

        try {

            // Solo aplicar a nuestra tabla
            if (!moduleDataTable || settings.nTable !== moduleDataTable.table().node()) {
                return true;
            }

            if (!filtrosActivos.length) return true;

            for (let filtro of filtrosActivos) {

                let columnasEvaluar = [];

                if (filtro.columna === "Todas") {
                    columnasEvaluar = data;
                } else {
                    const indexReal = parseInt(filtro.columna) + 1;

                    if (isNaN(indexReal) || !data[indexReal]) {
                        return true;
                    }

                    columnasEvaluar = [data[indexReal]];
                }

                let cumple = false;

                for (let valorCelda of columnasEvaluar) {

                    if (valorCelda === null || valorCelda === undefined) continue;

                    let celdaTexto = normalizarTexto(valorCelda);
                    let filtroTexto = normalizarTexto(filtro.valor);

                    switch (filtro.operador) {

                        // =========================
                        // TEXTO
                        // =========================
                        case "contiene":
                            cumple = celdaTexto.includes(filtroTexto);
                            break;

                        case "empieza con":
                            cumple = celdaTexto.startsWith(filtroTexto);
                            break;

                        case "termina con":
                            cumple = celdaTexto.endsWith(filtroTexto);
                            break;

                        case "igual a":
                            cumple = celdaTexto === filtroTexto;
                            break;

                        case "distinto a":
                            cumple = celdaTexto !== filtroTexto;
                            break;

                        // =========================
                        // NUMÉRICO
                        // =========================
                        case "menor que":
                            cumple = parseFloat(valorCelda) < parseFloat(filtro.valor);
                            break;

                        case "mayor que":
                            cumple = parseFloat(valorCelda) > parseFloat(filtro.valor);
                            break;

                        case "menor o igual que":
                            cumple = parseFloat(valorCelda) <= parseFloat(filtro.valor);
                            break;

                        case "mayor o igual que":
                            cumple = parseFloat(valorCelda) >= parseFloat(filtro.valor);
                            break;

                        // =========================
                        // FECHAS
                        // =========================
                        case "entre fechas":

                            if (!filtro.valor?.inicio || !filtro.valor?.fin) break;

                            const fechaCeldaEntre = parseDateES(valorCelda);
                            if (!fechaCeldaEntre) break;

                            const fechaInicio = new Date(filtro.valor.inicio + "T00:00:00");
                            const fechaFin = new Date(filtro.valor.fin + "T23:59:59");

                            cumple = fechaCeldaEntre >= fechaInicio && fechaCeldaEntre <= fechaFin;
                            break;

                        case "fecha menor que":

                            let fechaCeldaMenor = parseDateES(valorCelda);
                            if (!fechaCeldaMenor) break;

                            cumple = fechaCeldaMenor < new Date(filtro.valor + "T00:00:00");
                            break;

                        case "fecha mayor que":

                            let fechaCeldaMayor = parseDateES(valorCelda);
                            if (!fechaCeldaMayor) break;

                            cumple = fechaCeldaMayor > new Date(filtro.valor + "T23:59:59");
                            break;

                        case "fecha menor o igual que":

                            let fechaCeldaMenorIgual = parseDateES(valorCelda);
                            if (!fechaCeldaMenorIgual) break;

                            cumple = fechaCeldaMenorIgual <= new Date(filtro.valor + "T23:59:59");
                            break;

                        case "fecha mayor o igual que":

                            let fechaCeldaMayorIgual = parseDateES(valorCelda);
                            if (!fechaCeldaMayorIgual) break;

                            cumple = fechaCeldaMayorIgual >= new Date(filtro.valor + "T00:00:00");
                            break;
                    }

                    if (cumple) break;
                }

                if (!cumple) return false;
            }

            return true;

        } catch (error) {
            return true;
        }
    });


});


/* ============================================================
   Filtros personalizados
   ============================================================ */

function ajustarInputValorFiltro() {

    const operador = document.getElementById("operadorFiltro").value;
    const divFiltroContainer = document.getElementById("divFiltroContainer");

    if (!operador.includes("fecha")) {

        divFiltroContainer.innerHTML = `
            <label style="margin-bottom: 0px;color:black;"><strong>Valor</strong></label>
            <input type="text" id="valorFiltro" class="form-control form-control-sm" 
                onkeydown="if(event.keyCode == 13){ aplicarFiltroModulo(); }"
                placeholder="Valor a filtrar">
        `;

        return;
    }

    // =============================
    // ENTRE FECHAS
    // =============================
    if (operador === "entre fechas") {

        divFiltroContainer.innerHTML = `
            <label style="margin-bottom: 0px;color:black;"><strong>Valor</strong></label>
            <div style="display: flex; gap: 5px;">
                <input type="date" id="valorFiltroInicio" class="form-control form-control-sm">
                <input type="date" id="valorFiltroFin" class="form-control form-control-sm">
            </div>
        `;

        // 👇 IMPORTANTE: capturar después de crear
        const inputInicio = document.getElementById("valorFiltroInicio");
        const inputFin = document.getElementById("valorFiltroFin");

        inputInicio.addEventListener("change", function () {

            if (inputInicio.value) {
                inputFin.min = inputInicio.value;

                if (inputFin.value && inputFin.value < inputInicio.value) {
                    inputFin.value = "";
                }
            } else {
                inputFin.min = "";
            }
        });

        inputFin.addEventListener("change", function () {

            if (inputFin.value) {
                inputInicio.max = inputFin.value;

                if (inputInicio.value && inputInicio.value > inputFin.value) {
                    inputInicio.value = "";
                }
            } else {
                inputInicio.max = "";
            }
        });

        return;
    }

    // =============================
    // UNA SOLA FECHA
    // =============================
    divFiltroContainer.innerHTML = `
        <label style="margin-bottom: 0px;color:black;"><strong>Valor</strong></label>
        <input type="date" id="valorFiltro" class="form-control form-control-sm">
    `;
}




function aplicarFiltroModulo() {

    if (!moduleDataTable) return;

    const columna = document.getElementById("campoFiltro").value;
    const operador = document.getElementById("operadorFiltro").value;
    const acumular = document.getElementById("checkAcumularFiltros").checked;

    let valor = null;

    // =============================
    // ENTRE FECHAS
    // =============================
    if (operador === "entre fechas") {

        const inicio = document.getElementById("valorFiltroInicio")?.value;
        const fin = document.getElementById("valorFiltroFin")?.value;

        if (!inicio || !fin) return;

        valor = {
            inicio: inicio,
            fin: fin
        };
    }
    else {

        const input = document.getElementById("valorFiltro");
        if (!input || !input.value.trim()) return;

        valor = input.value.trim();
    }

    if (!acumular) {
        filtrosActivos = [];
    }

    filtrosActivos.push({
        columna: columna,
        operador: operador,
        valor: valor
    });

    actualizarFiltrosVisuales();
    moduleDataTable.draw();
}






function actualizarFiltrosVisuales() {

    const contenedor = document.getElementById("filtrosAplicados");

    if (!filtrosActivos.length) {
        contenedor.innerHTML = "No hay filtros aplicados";
        return;
    }

    let html = "<strong>Filtros aplicados:</strong><br>";

    filtrosActivos.forEach((filtro, index) => {
        let valorMostrar = "";
        if (filtro.operador === "entre fechas") {
            valorMostrar = `${filtro.valor.inicio} → ${filtro.valor.fin}`;
        } else {
            valorMostrar = filtro.valor;
        }

        html += `
        <span class="badge badge-info mr-2" style="margin-left:5px; height: 30px; margin-bottom:5px; font-size:12px; display: inline-flex; align-items: center;">
            ${dictColumnasFiltro[filtro.columna]} ${filtro.operador}: "${valorMostrar}"
            <a href="#" onclick="eliminarFiltro(${index})"
               style="color:white;margin-left:5px; font-size:14px;display: inline-flex; align-items: center;">×</a>
        </span>
    `;
    });


    contenedor.innerHTML = html;
}


function eliminarFiltro(index) {
    filtrosActivos.splice(index, 1);
    actualizarFiltrosVisuales();
    moduleDataTable.draw();
}


function limpiarFiltrosAplicados() {
    filtrosActivos = [];
    actualizarFiltrosVisuales();
    moduleDataTable.draw();
}

/* ============================================================
   Utilidad parseDateES
============================================================ */

function parseDateES(valor) {

    if (!valor) return null;

    valor = valor.trim();

    // dd/mm/yyyy
    const soloFecha = /^(\d{2})\/(\d{2})\/(\d{4})$/;

    // dd/mm/yyyy HH:mm
    const fechaHora = /^(\d{2})\/(\d{2})\/(\d{4})\s(\d{2}):(\d{2})$/;

    let match = valor.match(fechaHora);

    if (match) {
        const [, d, m, y, hh, mm] = match;
        return new Date(y, m - 1, d, hh, mm);
    }

    match = valor.match(soloFecha);

    if (match) {
        const [, d, m, y] = match;
        return new Date(y, m - 1, d);
    }

    return null;
}


function normalizarTexto(valor) {

    if (!valor) return "";

    return valor
        .toString()
        .normalize("NFD")                  // separa letras y tildes
        .replace(/[\u0300-\u036f]/g, "")   // elimina diacríticos
        .toLowerCase()
        .trim();
}



/* ============================================================
   Eliminar registro desde tabla
============================================================ */

document.addEventListener("click", function (e) {
    const btn = e.target.closest(".btn-delete-reg");

    if (!btn) return;

    const id = btn.dataset.id;
    const moduleId = btn.dataset.module;

    if (!id || !moduleId) {
        alert("Error: datos inválidos");
        return;
    }

    if (!confirm("¿Seguro que deseas eliminar este registro?")) {
        return;
    }
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

    fetch(`/module/${moduleId}/delete/${id}/`, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCSRFToken(),
        }
    })
        .then(response => response.json())
        .then(data => {

            if (data.success) {
                mostrarAlerta("success", data.message);

                // eliminar fila correctamente en DataTable
                const row = btn.closest("tr");

                if (moduleDataTable && row) {
                    moduleDataTable
                        .row(row)
                        .remove()
                        .draw(false);
                }

            } else {
                mostrarAlerta("danger", data.error || "Error al eliminar");
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-trash"></i>';
            }

        })
        .catch(error => {
            console.error("Error eliminando:", error);
            mostrarAlerta("danger", "Error de comunicación con el servidor");
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-trash"></i>';
        });
});


function mostrarAlerta(tipo, mensaje) {

    const container = document.querySelector(".container-fluid");

    if (!container) return;

    const alert = document.createElement("div");

    alert.className = `alert alert-${tipo} alert-dismissible fade show`;
    alert.innerText = mensaje;

    container.prepend(alert);

    setTimeout(() => {
        alert.classList.remove("show");

        setTimeout(() => {
            alert.remove();
        }, 300);
    }, 3000);
}