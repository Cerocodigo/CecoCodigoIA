let refInputActivo = null;
let refConfigActual = null;
let refTimeout = null;


let refRowsAll = [];
let refPageSize = 10;
let refCurrentPage = 1;
let refRowsOriginal = [];



const modalReferencia = new bootstrap.Modal(document.getElementById("modalReferencia"));

function abrirReferenciaBuscadorDetalle(btn) {
    refInputActivo = btn.closest(".input-group").querySelector("input");

    const modelo = refInputActivo.dataset.modelo;
    const campo = refInputActivo.dataset['name']

    refConfigActual = { modelo, campo };

    document.getElementById("refBuscadorInput").value = "";
    document.getElementById("refTablaHead").innerHTML = "";
    document.getElementById("refTablaBody").innerHTML = "";

    $('#modalReferencia').modal('show');
    buscarReferencia('')
}

function abrirReferenciaBuscador(btn) {
    refInputActivo = btn.closest(".input-group").querySelector("input");

    const modelo = refInputActivo.dataset.modelo;
    const campo = refInputActivo.name;

    refConfigActual = { modelo, campo };

    document.getElementById("refBuscadorInput").value = "";
    document.getElementById("refTablaHead").innerHTML = "";
    document.getElementById("refTablaBody").innerHTML = "";

    $('#modalReferencia').modal('show');
    buscarReferencia('')
}



function buscarReferenciaDirecto(q, refConfigActual, input) {
    const { modelo, campo } = refConfigActual;
    
    const tr = input.closest("tr");
    let filaEnvio = 0
    if(tr == null){
        filaEnvio = null
    }else{
        filaEnvio = tr.dataset['row']
    }

    fetch(`/calculosReferenciaBuscador/${modelo}/${campo}/${filaEnvio}/?q=${encodeURIComponent(q)}`, {
        headers: { "X-Requested-With": "XMLHttpRequest" }
    })
        .then(r => r.json())
        .then(data => {


            if(data.fila == null || data.fila == 'null'){
                //Cabecera
                refInputActivo = document.getElementById("id_" + data.Campo)
            }else{
                //Detalle
                const filas = document.querySelectorAll('tr[data-row="'+data.fila+'"]');

                filas.forEach(tr => {
                    const inputbuscador = tr.querySelector(`[data-name="${data.Campo}"]`);
                    if (inputbuscador) {
                        refInputActivo = inputbuscador
                    }
                });
            }


            if (!data.estado || !data.resultados || data.resultados.length == 0){
                                //asume detalle
                if (refInputActivo.parentElement.parentElement.tagName == 'TD') {

                    const tr = refInputActivo.closest("tr");

                    tr.querySelectorAll('input[data_tipo="ReferenciaAdjunto"]').forEach(campo => {
                        if (campo.dataset.refFrom === refInputActivo.dataset['name']) {
                                campo.value = '0'
                        }
                    });
                    calcular_Fila(tr)
                }
                //asume formulario
                if (refInputActivo.parentElement.parentElement.tagName == 'DIV') {
                    document
                        .querySelectorAll('input[data_tipo="ReferenciaAdjunto"]')
                        .forEach(campo => {
                            if (campo.dataset.refFrom === refInputActivo.dataset['name']) {
                                campo.value = '0'
                            }
                        });
                }

            }else{
                refInputActivo.value = data.resultados[0][refInputActivo.dataset['label_field']]
                refInputActivo.dataset['valor'] = data.resultados[0][refInputActivo.dataset['value_field']]

            

                //asume detalle
                if (refInputActivo.parentElement.parentElement.tagName == 'TD') {

                    const tr = refInputActivo.closest("tr");

                    tr.querySelectorAll('input[data_tipo="ReferenciaAdjunto"]').forEach(campo => {
                        if (campo.dataset.refFrom === refInputActivo.dataset['name']) {
                            if(campo.dataset.refKey in data.resultados[0]){
                                campo.value = data.resultados[0][campo.dataset.refKey] ?? "0";
                            }else{
                                campo.value = data.resultados[0][campo.dataset.refKey.toLowerCase()] ?? "0";
                            }
                        }
                    });
                    calcular_Fila(tr)
                }
                //asume formulario
                if (refInputActivo.parentElement.parentElement.tagName == 'DIV') {
                    document
                        .querySelectorAll('input[data_tipo="ReferenciaAdjunto"]')
                        .forEach(campo => {
                            if (campo.dataset.refFrom === refInputActivo.dataset['name']) {
                                if(campo.dataset.refKey in data.resultados[0]){
                                    campo.value = data.resultados[0][campo.dataset.refKey] ?? "0";
                                }else{
                                    campo.value = data.resultados[0][campo.dataset.refKey.toLowerCase()] ?? "0";
                                }
                            }
                        });
                }
            }
            
            calcularCabecera()


        });
}

function buscarReferencia(q) {
    const { modelo, campo } = refConfigActual;

    fetch(`/calculosReferenciaBuscador/${modelo}/${campo}/?q=${encodeURIComponent(q)}`, {
        headers: { "X-Requested-With": "XMLHttpRequest" }
    })
        .then(r => r.json())
        .then(data => {
            if (!data.estado || !data.resultados) return;
            renderTablaReferencia(data.resultados, data.Campos_filtros);
        });
}

function renderTablaReferencia(rows, Campos_filtros = []) {

    const head = document.getElementById("refTablaHead");
    const body = document.getElementById("refTablaBody");

    if (!rows || rows.length === 0) {
        head.innerHTML = `<tr><th>Resultado</th></tr>`;
        body.innerHTML = `<tr><td class="text-center text-muted">Sin resultados</td></tr>`;
        return;
    }

    refRowsAll = rows;
    refRowsOriginal = [...rows];
    refCurrentPage = 1;

    const columnas = Object.keys(rows[0]);

    // 👉 columnas visibles
    const columnasVisibles = Campos_filtros.length
        ? columnas.filter(c => Campos_filtros.includes(c))
        : columnas;

    // HEAD
    head.innerHTML = `
                <tr>
                    ${columnasVisibles.map(c => `<th>${c}</th>`).join("")}
                </tr>
            `;

    // guardar columnas visibles para el render paginado
    body._columnasVisibles = columnasVisibles;

    renderPaginaReferencia();
}

function filtrarReferenciaPorTexto(texto) {
    texto = texto.toLowerCase().trim();

    if (!texto) {
        refRowsAll = [...refRowsOriginal];
    } else {
        refRowsAll = refRowsOriginal.filter(row =>
            Object.values(row).some(v =>
                String(v ?? "")
                    .toLowerCase()
                    .includes(texto)
            )
        );
    }

    refCurrentPage = 1;
    renderPaginaReferencia();
}

function renderPaginaReferencia() {
    const body = document.getElementById("refTablaBody");
    const info = document.getElementById("refPageInfo");

    body.innerHTML = "";

    const columnas = body._columnasVisibles || Object.keys(refRowsAll[0]);

    const start = (refCurrentPage - 1) * refPageSize;
    const end = start + refPageSize;
    const pageRows = refRowsAll.slice(start, end);

    pageRows.forEach((row, index) => {
        const tr = document.createElement("tr");
        tr.dataset.index = start + index;

        tr.innerHTML = columnas
            .map(c => `<td>${row[c] ?? ""}</td>`)
            .join("");

        body.appendChild(tr);
    });

    const totalPages = Math.ceil(refRowsAll.length / refPageSize);
    info.textContent = `Página ${refCurrentPage} de ${totalPages}`;

    document.getElementById("refPrevBtn").disabled = refCurrentPage === 1;
    document.getElementById("refNextBtn").disabled = refCurrentPage === totalPages;

    body._rowsData = refRowsAll;
}

function seleccionarReferencia(row) {
    // 🔑 Asumimos value_field = ClienteId
    refInputActivo.value = row[refInputActivo.dataset['label_field']]
    refInputActivo.dataset['valor'] = row[refInputActivo.dataset['value_field']]

    //asume detalle
    if (refInputActivo.parentElement.parentElement.tagName == 'TD') {

        const tr = refInputActivo.closest("tr");

        tr.querySelectorAll('input[data_tipo="ReferenciaAdjunto"]').forEach(campo => {
            if (campo.dataset.refFrom === refInputActivo.dataset['name']) {

                if(campo.dataset.refKey in row){
                    campo.value = row[campo.dataset.refKey] ?? "0";
                }else{
                    campo.value = row[campo.dataset.refKey.toLowerCase()] ?? "0";
                }
                // campo.dispatchEvent(new Event("change")); // opcional
            }
        });
        calcular_Fila(tr)
    }
    //asume formulario
    if (refInputActivo.parentElement.parentElement.tagName == 'DIV') {
        document
            .querySelectorAll('input[data_tipo="ReferenciaAdjunto"]')
            .forEach(campo => {

                if (campo.dataset.refFrom === refInputActivo.dataset['name']) {

                    if(campo.dataset.refKey in row){
                        campo.value = row[campo.dataset.refKey] ?? "0";
                    }else{
                        campo.value = row[campo.dataset.refKey.toLowerCase()] ?? "0";
                    }
                    //campo.dispatchEvent(new Event("change")); // opcional
                }
            });
    }
    // 🔥 Aplicar referencias adjuntas
    calcularCabecera()

    document.getElementById("BtnClosemodalReferencia").click();
}

function calcular_Fila(tr) {

    // 1️⃣ Mapa de valores de la fila
    const valores = {};

    tr.querySelectorAll('input, select, textarea').forEach(el => {
        if (!el.name) return;

        let val = el.value;

        if (val !== "" && !isNaN(val)) {
            val = parseFloat(val);
        }

        valores[el.dataset['name']] = val;
    });

    // 2️⃣ Procesar campos operativos
    tr.querySelectorAll('input').forEach(campo => {

        const tipo = campo.attributes.data_tipo.value;

        // 🔢 Operacion
        if (tipo === 'Operacion') {
            const formula = campo.dataset.formula; // "Cantidad * ItemPvp"
            if (!formula) return;

            const resultado = calcular_valor_Operacion(formula, valores);

            if (resultado !== null && !isNaN(resultado)) {
                valores[campo.dataset['name']] = resultado;
                campo.value = resultado;
                //campo.dispatchEvent(new Event('change'));
            }
        }

        // 🧮 Formula (placeholder para siguiente nivel)
        if (tipo === 'Formula') {
            // aquí luego puedes usar funciones tipo SUM, AVG, etc. no aplica a detalle si ni existe subdetalle
        }

        // 🔤 Número a letras
        if (tipo === 'TraductorNumeroLetras') {
            // ejemplo futuro: campo.value = numeroALetras(valorOrigen)
        }

        // 🔀 Condicional
        if (tipo === 'Condicional') {
            // ejemplo: if (condicion) campo.value = X
            // ---- CONDICIONES ----
            let data_condiciones = campo.dataset.condiciones || '[]';

            try {
                data_condiciones = data_condiciones.replace(/([{,]\s*)'([^']+?)'\s*:/g, '$1"$2":').replace(/:\s*'([^']+?)'/g, ': "$1"')             // valores simples
                data_condiciones = JSON.parse(data_condiciones);
            } catch (e) {
                console.warn('Condiciones inválidas:', campo.dataset.condiciones);
                data_condiciones = [];
            }

            // ---- SI NO ----
            let data_si_no = campo.dataset.si_no ?? null;
            if (!isNaN(data_si_no)) data_si_no = Number(data_si_no);

            let resultado = data_si_no;

            // ---- EVALUACIÓN ----
            if (Array.isArray(data_condiciones)) {

                for (const regla of data_condiciones) {

                    const valorCampo = valoresCab[regla.si.campo];
                    let cumple = false;

                    switch (regla.si.operador) {
                        case '==':
                            cumple = valorCampo == regla.si.valor;
                            break;
                        case '!=':
                            cumple = valorCampo != regla.si.valor;
                            break;
                        case '>':
                            cumple = Number(valorCampo) > Number(regla.si.valor);
                            break;
                        case '<':
                            cumple = Number(valorCampo) < Number(regla.si.valor);
                            break;
                        case '>=':
                            cumple = Number(valorCampo) >= Number(regla.si.valor);
                            break;
                        case '<=':
                            cumple = Number(valorCampo) <= Number(regla.si.valor);
                            break;
                        case 'in':
                            cumple = Array.isArray(regla.si.valor)
                                && regla.si.valor.includes(valorCampo);
                            break;
                    }

                    if (cumple) {
                        resultado = regla.entonces;
                        break; // primera condición válida
                    }
                }
            }

            campo.value = resultado;
        }
    });
}

function calcular_valor_Operacion(formula, valores) {
    let expr = formula;

    Object.keys(valores).forEach(key => {
        const val = valores[key] ?? 0;
        const regex = new RegExp(`\\b${key}\\b`, 'g');
        expr = expr.replace(regex, val);
    });

    // Seguridad básica
    if (/[^0-9+\-*/().\s]/.test(expr)) return null;

    try {
        return Function(`"use strict"; return (${expr})`)();
    } catch (e) {
        console.warn('Error en fórmula:', formula, e);
        return null;
    }
}

function calcularCabecera() {
    const valoresCab = {};

    document
        .querySelectorAll('#cabeceraNorte input, #cabeceraNorte select, #cabeceraNorte textarea, #cabeceraSur input, #cabeceraSur select, #cabeceraSur textarea')
        .forEach(campo => {

            if (!campo.name) return;

            let valor = campo.value;

            // convertir a número si aplica
            if (valor !== '' && !isNaN(valor)) {
                valor = parseFloat(valor);
            }

            valoresCab[campo.name] = valor;
        });

    // 2️⃣ Procesar campos operativos
    document.querySelectorAll('#cabeceraNorte input, #cabeceraNorte select, #cabeceraNorte textarea, #cabeceraSur input, #cabeceraSur select, #cabeceraSur textarea').forEach(campo => {
        const tipo = campo.attributes.data_tipo.value;


        if (tipo === 'FormatoTexto') {

            const template = campo.dataset.template;

            // padding viene como string
            let padding = campo.dataset.padding;

            // convertir a objeto
            try {
                padding = padding.replace(/'/g, '"');
                padding = JSON.parse(padding);
            } catch (e) {
                console.warn('Padding inválido:', campo.dataset.padding);
                padding = {};
            }

            let resultado = template;

            Object.keys(padding).forEach(k => {
                const val = valoresCab[k] ?? '';
                resultado = resultado.replace(
                    new RegExp(`\\{${k}\\}`, 'g'), // reemplaza todas
                    String(val).padStart(padding[k], '0')
                );
            });

            campo.value = resultado;
        }

        // 🔢 Operacion
        if (tipo === 'Operacion') {
            const formula = campo.dataset.formula; // "Cantidad * ItemPvp"
            if (!formula) return;

            const resultado = calcular_valor_Operacion(formula, valoresCab);

            if (resultado !== null && !isNaN(resultado)) {
                valoresCab[campo.name] = resultado.toFixed(campo.dataset['decimales']);
                campo.value = resultado.toFixed(campo.dataset['decimales']);
                //campo.dispatchEvent(new Event('change'));
            }
        }

        // 🧮 Formula (placeholder para siguiente nivel)
        if (tipo === 'FormulaDetalle') {

            valoresCab[campo.dataset['name']] = aplicarOperacionFormulaDetalle(campo).toFixed(campo.dataset['decimales'])
            campo.value = valoresCab[campo.dataset['name']]

            
        }

        // 🔤 Número a letras
        if (tipo === 'TraductorNumeroLetras') {
            // ejemplo futuro: campo.value = numeroALetras(valorOrigen)
        }

        // 🔀 Condicional
        if (tipo === 'Condicional') {
            // ejemplo: if (condicion) campo.value = X
            // ejemplo: if (condicion) campo.value = X
            // ---- CONDICIONES ----
            let data_condiciones = campo.dataset.condiciones || '[]';

            try {

                data_condiciones = data_condiciones.replace(/([{,]\s*)'([^']+?)'\s*:/g, '$1"$2":').replace(/:\s*'([^']+?)'/g, ': "$1"')             // valores simples

                data_condiciones = JSON.parse(data_condiciones);

            } catch (e) {
                console.warn('Condiciones inválidas:', campo.dataset.condiciones);
                data_condiciones = [];
            }

            // ---- SI NO ----
            let data_si_no = campo.dataset.si_no ?? null;
            if (!isNaN(data_si_no)) data_si_no = Number(data_si_no);

            let resultado = data_si_no;

            // ---- EVALUACIÓN ----
            if (Array.isArray(data_condiciones)) {

                for (const regla of data_condiciones) {

                    const valorCampo = valoresCab[regla.si.campo];
                    let cumple = false;

                    switch (regla.si.operador) {
                        case '==':
                            cumple = valorCampo == regla.si.valor;
                            break;
                        case '!=':
                            cumple = valorCampo != regla.si.valor;
                            break;
                        case '>':
                            cumple = Number(valorCampo) > Number(regla.si.valor);
                            break;
                        case '<':
                            cumple = Number(valorCampo) < Number(regla.si.valor);
                            break;
                        case '>=':
                            cumple = Number(valorCampo) >= Number(regla.si.valor);
                            break;
                        case '<=':
                            cumple = Number(valorCampo) <= Number(regla.si.valor);
                            break;
                        case 'in':
                            cumple = Array.isArray(regla.si.valor)
                                && regla.si.valor.includes(valorCampo);
                            break;
                    }

                    if (cumple) {
                        resultado = regla.entonces;
                        break; // primera condición válida
                    }
                }
            }

            campo.value = resultado;
        }
    });




    return valoresCab;
}

function calcular_masivoCabecera() {

    calcularCabecera()

    const tabla = document.getElementById('tabla-detalles');
    if (!tabla) return;

    tabla.querySelectorAll('tbody tr').forEach(tr => {
        calcular_Fila(tr);
    });

    calcularCabecera()


}


function evaluarCondicion(tr, condicion) {
    //const match = condicion.match(/^(\w+)\s*(=|>=|<=|>|<)\s*(\d+(\.\d+)?)$/);
    const match = condicion.match(/^(\w+)\s*(==|=|>=|<=|>|<)\s*(-?\d+(\.\d+)?)$/);
    if (!match) return true;

    const campoCond = match[1];
    const operador = match[2];
    const valorCond = parseFloat(match[3]);

    const inputCampo = tr.querySelector(
        `[data-campo="${campoCond}"], [data-name="${campoCond}"]`
    );

    if (!inputCampo) return false;

    const valorFila = parseFloat(inputCampo.value || inputCampo.textContent || 0);

    switch (operador) {
        case "=": return valorFila === valorCond;
        case "==": return valorFila === valorCond;
        case ">": return valorFila > valorCond;
        case "<": return valorFila < valorCond;
        case ">=": return valorFila >= valorCond;
        case "<=": return valorFila <= valorCond;
        
        default: return false;
    }
}

function aplicarOperacionFormulaDetalle(input) {
    const operacion = input.dataset.operacion;      // SUM
    const campo = input.dataset.campo;              // Subtotal
    const tablaKey  = input.dataset.tabla;            // ventasfacturasdetalle
    const condicion = input.dataset.condicion;      // ejemplo: tarifaiva > 0

    let total = 0;

    // obtener tabla (DataTable o normal)
    const tabla = document.getElementById(`tabla-detalles-${tablaKey}`);
    if (!tabla) return;

    const filas = tabla.querySelectorAll("tbody tr");

    filas.forEach(tr => {
        let cumple = true;

        // ===== evaluar condición =====
        if (condicion) {
            cumple = evaluarCondicion(tr, condicion);
        }

        if (cumple) {
            const inputCampo = tr.querySelector(`[data-name="${campo}"], [data-campo="${campo}"]`);
            if (inputCampo) {
                const valor = parseFloat(inputCampo.value || inputCampo.textContent || 0);
                if (!isNaN(valor)) {
                    if (operacion === "SUM") {
                        total += valor;
                    }
                }
            }
        }
    });

    return total
}

document.getElementById("BtnClosemodalReferencia").addEventListener("click", () => {
    const input = document.getElementById("refBuscadorInput");
    input.value = "";

    refRowsAll = [...refRowsOriginal];
    refCurrentPage = 1;
    renderPaginaReferencia();

});

document.getElementById("refBuscadorInput").addEventListener("keydown", e => {
    if (e.key === "Enter") {
        e.preventDefault();
        filtrarReferenciaPorTexto(e.target.value);
    }
});

document.getElementById("refPrevBtn").addEventListener("click", () => {
    if (refCurrentPage > 1) {
        refCurrentPage--;
        renderPaginaReferencia();
    }
});

document.getElementById("refNextBtn").addEventListener("click", () => {
    const totalPages = Math.ceil(refRowsAll.length / refPageSize);
    if (refCurrentPage < totalPages) {
        refCurrentPage++;
        renderPaginaReferencia();
    }
});


document.addEventListener("change", function (e) {
    const input = e.target;

    // 🎯 solo inputs tipo ReferenciaBuscador
    if (input.tagName === "INPUT") {
        if (input.attributes.getNamedItem('data_tipo') != null) {
            if (input.attributes.data_tipo.value === "ReferenciaBuscador") {

                const refInputActivo = input;
                const modelo = refInputActivo.dataset.modelo;
                const campo =  refInputActivo.dataset['name']
                //const campo = refInputActivo.name;
                
                const q = input.value.trim();

                if (q.length < 2) return;

                buscarReferenciaDirecto(q, { modelo, campo }, input);

                calcular_masivoCabecera()

            }
            if (input.attributes.data_tipo.value === "NumeroSimple") {
                if (input.parentElement.parentElement.tagName == 'TR') {
                    calcular_Fila(input.parentElement.parentElement)

                }
                if (input.parentElement.parentElement.tagName == 'DIV') {
                    calcular_masivoCabecera()
                }
            }
        }
    }



    if (e.target.classList.contains("input-archivo")) {

        const input = e.target
        const file = input.files[0]

        if (!file) return

        const empresa = document.getElementById("ccidempresa").value

        const formData = new FormData()
        formData.append("archivo", file)
        formData.append("campo", input.name)
        formData.append("empresa", empresa)

        fetch("/module/subir_archivo/", {
            method: "POST",
            headers: {
                "X-CSRFToken": getCookie("csrftoken")
            },
            body: formData
        })
            .then(response => response.json())
            .then(data => {

                if (data.estado) {

                    const hidden = document.getElementById("hidden_" + input.name)

                    if (hidden) {
                        hidden.value = data.ruta
                    }

                    if (file.type.startsWith("image/")) {

                        const preview = document.getElementById("preview_" + input.name)

                        if (preview) {
                            preview.src = data.url
                            preview.style.display = "block"
                        }

                    }

                }

            })

    }

    //busca aplicar las referencias adjuntos sobre los adjutos del select
    if (input.tagName === "SELECT") {

        const opt = e.target.options[e.target.selectedIndex];
        if (!opt) return;

        const fila = e.target.closest('tr');
        const scope = fila || document;

        scope.querySelectorAll('[data-ref-from]').forEach(el => {
            if (el.dataset.refFrom === e.target.dataset['name']) {
                if(el.dataset.refKey in opt.dataset){
                    el.value = opt.dataset[el.dataset.refKey] || '';
                    cambioVariableparaQueary(el.dataset['name'])

                }else{
                    console.warn("Referencia no encontrada", {
                    campo: input,
                    elemento_id: el.id,
                    ref_key: el.dataset.refKey,
                    opciones: opt.dataset
                    });
                }
                
            }
        });
    }

    //revisa si el input fue realizado cobre un dato variable para ejecutar QueryBaseDatos

    cambioVariableparaQueary(e.target.dataset['name'])
    calcularCabecera()
})


function cambioVariableparaQueary(campoCambiado){

    if (!campoCambiado) return;

    document.querySelectorAll('[data_tipo="QueryBaseDatos"]').forEach(input => {
        const variables = input.dataset.variables;
        if (!variables) return;

        const deps = variables.split(",").map(v => v.trim());

        // ✅ Solo si el campo cambiado es dependencia
        if (deps.includes(campoCambiado)) {
            EjecutarQueryBaseDatos(input);
        }
    });

}


function getCookie(name) {

    let cookieValue = null

    if (document.cookie && document.cookie !== "") {

        const cookies = document.cookie.split(";")

        for (let i = 0; i < cookies.length; i++) {

            const cookie = cookies[i].trim()

            if (cookie.substring(0, name.length + 1) === (name + "=")) {

                cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
                break

            }

        }

    }

    return cookieValue
}

document.getElementById("refTablaBody").addEventListener("click", function (e) {
    const tr = e.target.closest("tr");
    if (!tr) return;

    const index = tr.dataset.index;
    const row = this._rowsData[index];

    seleccionarReferencia(row);
});


function getCSRFToken() { return document.getElementsByName('csrfmiddlewaretoken')[0].value }


document.addEventListener("input", function (e) {
    const input = e.target;
    if (!input.matches('[data_tipo="ReferenciaBuscador"]')) return;

    const value = input.value.trim();
    if (value.length < 2) return;

    const referencia = input.dataset.referencia;
    if (!referencia) {
        console.warn("Referencia no definida", input);
        return;
    }

    fetch(`/buscarReferencia/${referencia}/?q=${encodeURIComponent(value)}`, {
        headers: { "X-Requested-With": "XMLHttpRequest" }
    })
        .then(r => r.json())
        .then(data => {
            mostrarSugerencias(input, data);
        })
        .catch(err => console.error("Error buscador:", err));
});


/* =========================================================
   🧭 UTILIDADES DE FECHA
========================================================= */
function fechaLocal() {
    const d = new Date();
    const pad = n => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function fechaHoraLocal() {
    const d = new Date();
    const pad = n => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/* =========================================================
   🔢 NUMÉRICOS → FORZAR MÍNIMO
========================================================= */
function aplicarMinimoNumerico(el) {
    if (el.type !== 'number') return;

    const min = el.dataset.min !== '' ? Number(el.dataset.min) : 0;
    let value = Number(el.value);

    if (isNaN(value) || el.value === '') {
        el.value = min;
        return;
    }
    if (value < min) el.value = min;
}

/* =========================================================
   🔥 REGLAS GENERALES EN UN SCOPE
========================================================= */
function aplicarReglasEnScope(scope) {
    scope.querySelectorAll('input[type="number"]').forEach(aplicarMinimoNumerico);

    scope.querySelectorAll('input[type="date"]').forEach(el => {
        if (!el.value) el.value = fechaLocal();
    });

    scope.querySelectorAll('input[type="datetime-local"]').forEach(el => {
        if (!el.value) el.value = fechaHoraLocal();
    });

    scope.querySelectorAll('[data_tipo="SistemaFecha"]').forEach(el => {
        if (!el.value) el.value = fechaHoraLocal();
    });

    scope.querySelectorAll('[data_tipo="SistemaUsuario"]').forEach(el => {
        // if (!el.value) el.value = '{{usuario}}'
        if (!el.value) el.value = window.APP?.user?.firstName || 'Usuario';
    });
}

/* =========================================================
   ➕➖ DETALLES (FILAS DINÁMICAS)
========================================================= */
/* =========================================================
   ➕➖ DETALLES (FILAS DINÁMICAS MULTITAB)
========================================================= */

function adicionarFila(e) {
    const btn = e.currentTarget;

    const tabPane = btn.closest('.tab-pane');
    const container = tabPane.querySelector('.detalles-container');

    if (!container) return;

    const filaBase = container.querySelector('.detalle-fila');
    if (!filaBase) return;

    const filaspMax = Array.from(
        document.querySelectorAll(`tr[data-form="${filaBase.dataset.form}"]`)
    );

    const maxRow = filaspMax.length
        ? Math.max(...filaspMax.map(f => +f.dataset.row || 0))
        : 0;

    const nuevaFila = filaBase.cloneNode(true);
    nuevaFila.dataset.row = maxRow + 1;
    const nuevoIndex = maxRow + 1;

    nuevaFila.querySelectorAll('input, select, textarea').forEach(el => {

        // limpiar valores
        if (el.type === 'checkbox' || el.type === 'radio') {
            el.checked = false;
        } else {
            el.value = '';
        }

        // 🔥 ACTUALIZAR NAME (AQUÍ EL FIX REAL)
        if (el.name) {
            el.name = el.name.replace(/_(\d+)-/, `_${nuevoIndex}-`);
        }
        // 🔥 ACTUALIZAR ID
        if (el.id) {
            el.id = el.id.replace(/_(\d+)-/, `_${nuevoIndex}-`);
        }
      
    });

    aplicarReglasEnScope(nuevaFila);
    container.appendChild(nuevaFila);
        // 🔥 AQUÍ EL FOCUS
    const primerInput = nuevaFila.querySelector(
        'input:not([type="hidden"]), select, textarea'
    );

    if (primerInput) {
        primerInput.focus();
    }
}

function inicializarDetalles() {

    document.querySelectorAll('.agregar-fila').forEach(btnAgregar => {
        btnAgregar.addEventListener('click', adicionarFila);
    });

    // eliminar fila
    document.addEventListener('click', function (e) {

        if (!e.target.closest('.eliminar-fila')) return;

        const fila = e.target.closest('.detalle-fila');

        const container = fila.closest('.detalles-container');
        


        const filas = container.querySelectorAll('.detalle-fila');

        if (filas.length > 1) {
            fila.remove();
        } else {
            alert('Debe existir al menos una fila');
        }

    });

    // validación numérica
    document.addEventListener('input', function (e) {

        if (e.target.matches('input[type="number"]')) {
            aplicarMinimoNumerico(e.target);
        }

    });

    // aplicar reglas iniciales
    document.querySelectorAll('.detalles-container').forEach(container => {
        aplicarReglasEnScope(container);
    });

}


/* =========================================================
   🔍 SELECT2
========================================================= */
/* =========================================================
   🔢 Campo Consolidado Query (⭐ LO IMPORTANTE ⭐)
========================================================= */
function EjecutarQueryBaseDatos(input) {


    // 🔁 Si ya tiene valor, no recalcular
    const modelo = input.dataset.modelo;
    const campo = input.name || input.dataset.campo;

    if (!modelo || !campo) {
        console.warn("QueryBaseDatos mal configurado", input);
        return;
    }

    // 📦 Recolectar variables dependientes
    const payload = {};
    const variables = input.dataset.variables;

    if (variables) {
        variables.split(",").forEach(nombreCampo => {
            const origen = document.querySelector(
                `[name="${nombreCampo}"], [data-campo="${nombreCampo}"]`
            );
            if (origen) {
                payload[nombreCampo] = origen.value;
            }
        });
    }

    fetch(`/calculosQueryBaseDatos/${modelo}/${campo}/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": getCSRFToken()   // 🔥 CLAVE
        },
        body: JSON.stringify(payload)
    })
        .then(r => r.json())
        .then(data => {
            if (data.estado && data.tipo === "QueryBaseDatos") {
                input.value = data.valor ?? "";
                calcularCabecera()
            }
        })
        .catch(err => console.error("Error QueryBaseDatos:", err));

}


/* =========================================================
   🔢 Texto Inicial (⭐ LO IMPORTANTE ⭐)
========================================================= */
function inicializarValoresTexto_inicial() {

    
    document.querySelectorAll('[data_tipo="TextoSimple"]').forEach(input => {
        if (input.value) return;

        if(input.value ===""){
            input.value = input.dataset['valor_predeterminado']
        }

    });
}
/* =========================================================
   🔢 Referencia Inicial (⭐ LO IMPORTANTE ⭐)
========================================================= */
function inicializarReferenciasValor_inicial() {

    
    document.querySelectorAll('[data_tipo="ReferenciaBuscador"]').forEach(input => {
        if (input.value.length > 0) return;

        const modelo = input.dataset.modelo;
        const campo = input.name || input.dataset.campo;

        if (input.hasAttribute('data-valorinicial')) {
            const valorInicial = input.getAttribute('data-valorinicial');
            if (valorInicial.length > 0) {

                buscarReferenciaDirecto(valorInicial, { modelo, campo }, input);

            }

        }

    });
}
/* =========================================================
   🔢 NUMERO SECUENCIAL (⭐ LO IMPORTANTE ⭐)
========================================================= */
function inicializarNumerosSecuenciales() {
    document.querySelectorAll('[data_tipo="NumeroSecuencial"]').forEach(input => {
        if (input.value) return;

        const modelo = input.dataset.modelo;
        const campo = input.name || input.dataset.campo;



        if (!modelo || !campo) {
            console.warn("Campo secuencial mal configurado", input);
            return;
        }

        fetch(`/calculosCampos/${modelo}/${campo}/`, {
            headers: { "X-Requested-With": "XMLHttpRequest" }
        })
            .then(r => r.json())
            .then(data => {
                if (data.estado && data.tipo === "NumeroSecuencial") {
                    input.value = data.siguiente;
                }
            })
            .catch(err => console.error("Error secuencial:", err));
    });
}

/* =========================================================
   🚀 INICIALIZACIÓN GENERAL
========================================================= */
document.addEventListener('DOMContentLoaded', () => {
    // =========================
    // Auto cerrar alertas
    // =========================
    const alert = document.getElementById("registerAlert");
    if (alert) {
        setTimeout(() => {
        alert.classList.remove("show");

        setTimeout(() => {
            alert.remove();
        }, 300);

    }, 2500);
    }

    inicializarNumerosSecuenciales();
    inicializarDetalles();
    inicializarReferenciasValor_inicial();
    inicializarValoresTexto_inicial();

    // 🔥 aplicar referencias al inicio
    document.querySelectorAll('select[data-ref-source]').forEach(select => {
        select.dispatchEvent(new Event('change', { bubbles: true }));
    });

    // 🔥 reglas generales cabecera
    aplicarReglasEnScope(document);
});




document.addEventListener("keydown", function(e) {
    if (e.key === "Enter") {
        e.preventDefault();

        const inputs = Array.from(document.querySelectorAll("input, select, textarea"));
        const index = inputs.indexOf(document.activeElement);

        if (index > -1 && index < inputs.length - 1) {
            inputs[index + 1].focus();
        }

        const elemento = e.target;

        const filaActual = elemento.closest('tr.detalle-fila');
        if (!filaActual) return;

        const container = filaActual.closest('.detalles-container');
        if (!container) return;

        const celdaActual = elemento.closest('td');
        if (!celdaActual) return;

        // 🔥 solo celdas visibles (sin .d-none)
        const celdasVisibles = Array.from(
            filaActual.querySelectorAll('td:not(.d-none)')
        );

        // 🔥 primera celda visible
        const primeraCelda = celdasVisibles[0];

        if (celdaActual !== primeraCelda) return;

        const filas = Array.from(container.querySelectorAll('tr.detalle-fila'));
        const ultimaFila = filas[filas.length - 1];

        if (filaActual === ultimaFila) {
            adicionarFilaDesdeElemento(elemento);
        }
        e.preventDefault();
        
    }
});
function adicionarFilaDesdeElemento(elemento) {
    const tabPane = elemento.closest('.tab-pane');
    if (!tabPane) return;

    const container = tabPane.querySelector('.detalles-container');
    if (!container) return;

    const filas = container.querySelectorAll('.detalle-fila');
    const nuevaIndex = filas.length; // 👈 índice real

    const filaBase = filas[0];
    if (!filaBase) return;

    const nuevaFila = filaBase.cloneNode(true);

    nuevaFila.dataset.row = nuevaIndex;
    nuevaFila.dataset.form = nuevaIndex;

    nuevaFila.querySelectorAll('input, select, textarea').forEach(el => {

        // 🔥 LIMPIAR VALORES
        if (el.type === 'checkbox' || el.type === 'radio') {
            el.checked = false;
        } else {
            el.value = '';
        }

        // 🔥 ACTUALIZAR NAME
        if (el.name) {
            el.name = el.name.replace(/_(\d+)-/, `_${nuevaIndex}-`);
        }
        // 🔥 ACTUALIZAR ID
        if (el.id) {
            el.id = el.id.replace(/_(\d+)-/, `_${nuevaIndex}-`);
        }
      
    });

    aplicarReglasEnScope(nuevaFila);
    container.appendChild(nuevaFila);

    const primerInput = nuevaFila.querySelector(
        'input:not([type="hidden"]), select, textarea'
    );

    if (primerInput) primerInput.focus();
}
