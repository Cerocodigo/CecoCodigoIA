let MODULE_DATA = null;
let PDF_TEMPLATES = null;

document.addEventListener("DOMContentLoaded", () => {
    const moduleEl = document.getElementById("module-data");
    const templatesEl = document.getElementById("pdf-templates-data");

    if (moduleEl) MODULE_DATA = JSON.parse(moduleEl.textContent);
    if (templatesEl) PDF_TEMPLATES = JSON.parse(templatesEl.textContent);
});

// ======================================================
// ENTRY
// ======================================================

function obtener_datos_pdf_registro(plantillaId) {

    const plantilla = PDF_TEMPLATES.find(p => p.id === plantillaId || p._id === plantillaId);

    const data = {
        metadata: MODULE_DATA,
        plantilla_pdf: plantilla,
        valores_cab: obtener_valores_cabecera(),
        valores_det: obtener_valores_detalle()
    };

    generar_pdf_registro(data);
}

// ======================================================
// DATA
// ======================================================

function obtener_valores_cabecera() {
    const data = {};

    ["cabeceraNorte", "cabeceraSur"].forEach(id => {
        const container = document.getElementById(id);
        if (!container) return;

        container.querySelectorAll("input, select, textarea").forEach(el => {
            if (!el.name) return;

            if (el.type === "checkbox") {
                data[el.name] = el.checked;
            }
            else if (el.type === "radio") {
                if (el.checked) {
                    data[el.name] = el.value;
                }
            }
            else {
                data[el.name] = el.value;
            }
        });
    });

    return data;
}

function obtener_valores_detalle() {
    const resultado = {};

    document.querySelectorAll(".tab-pane[id^='tab_content']").forEach(tab => {

        const modeloId = tab.id.replace("tab_content", "");
        const filas = tab.querySelectorAll("tbody .detalle-fila");

        const registros = [];

        filas.forEach((fila, i) => {
            const obj = {};

            fila.querySelectorAll("input, select, textarea").forEach(el => {
                if (!el.name) return;

                let campo = el.name.includes("-") ? el.name.split("-")[1] : el.name;

                if (el.type === "checkbox") obj[campo] = el.checked;
                else if (el.type === "radio") {
                    if (el.checked) obj[campo] = el.value;
                } else obj[campo] = el.value;
            });

            if (Object.keys(obj).length) registros.push(obj);
        });

        if (registros.length) resultado[modeloId] = registros;
    });

    return resultado;
}

// ======================================================
// MOTOR
// ======================================================

function generar_pdf_registro(data) {

    const plantilla = data.plantilla_pdf;
    const pagina = plantilla.pagina;
    const segs = plantilla.segmentos;

    const cab = data.valores_cab;
    const det = data.valores_det;

    const ancho = parseFloat(pagina.ancho);
    const largo = parseFloat(pagina.largo);

    const doc = new jspdf.jsPDF(
        ancho > largo ? "l" : "p",
        pagina.unidades || "cm",
        [largo, ancho]
    );

    doc.setFont("helvetica");
    doc.setFontSize(parseFloat(pagina.letra || 10));

    let y = 1;

    // ======================================================
    // CABECERA
    // ======================================================

    if (segs.cabecera) {
        y += renderSegmento(doc, segs.cabecera, cab, y);
    }

    // ======================================================
    // DETALLE
    // ======================================================

    if (Array.isArray(segs.detalle)) {

        segs.detalle.forEach(seg => {
            console.log("------------------------------------------");
            console.log("Procesando segmento detalle para tabla:", seg.tabla);
            console.log("------------------------------------------");

            const registros = det[seg.tabla];
            if (!registros) return;

            y += parseFloat(seg.alturaInicial || 0);

            // =====================================
            // CABECERAS DE COLUMNAS
            // =====================================

            doc.setFont(undefined, "bold");

            seg.columnas.forEach(col => {

                const x = parseFloat(col.x);
                const align = (col.orientacion || "izquierda") === "derecha"
                    ? "right"
                    : "left";

                doc.text(col.cabecera || "", x, y, { align });
            });

            doc.setFont(undefined, "normal");
            y += 0.5;

            // =====================================
            // FILAS
            // =====================================

            registros.forEach(row => {

                let alturaFila = 0.5;

                seg.columnas.forEach(col => {

                    const valor = devolver_valor_imp(
                        row[col.campo],
                        col.tipo,
                        col.formato
                    );

                    const x = parseFloat(col.x);
                    doc.setFontSize(parseFloat(col.tamano || 8));

                    if (col.tipo === "Imagen") {

                        const img = document.getElementById(`preview_${col.campo}`);

                        if (img && img.src) {
                            const base64 = getBase64ImagePdf(img);

                            const w = parseFloat(col.largoMaximo || 1);
                            const h = parseFloat(col.filasMaximas || 1);

                            doc.addImage(base64, "PNG", x, y, w, h);
                            alturaFila = Math.max(alturaFila, h);
                        }
                    }
                    else {

                        const lines = obtenerLineasTexto(
                            doc,
                            valor,
                            col.largoMaximo,
                            null
                        );

                        const align = (col.orientacion || "izquierda") === "derecha"
                            ? "right"
                            : "left";

                        doc.text(lines, x, y, { align });

                        const alturaTexto = calcularAlturaTexto(
                            doc,
                            lines,
                            parseFloat(col.tamano || 8)
                        );

                        alturaFila = Math.max(alturaFila, alturaTexto);
                    }
                });

                y += alturaFila;

                if (y > largo - 2) {
                    doc.addPage();
                    y = 2;
                }
            });
        });
    }

    // ======================================================
    // PIE
    // ======================================================

    if (segs.pie) {

        let altura = estimarAlturaSegmento(segs.pie);

        if (segs.pie.positionFixed) {
            renderSegmento(doc, segs.pie, cab, largo - altura - 1);
        } else {
            y += parseFloat(segs.pie.alturaInicial || 0);
            y += renderSegmento(doc, segs.pie, cab, y);
        }
    }

    // ======================================================
    // SAVE
    // ======================================================

    // doc.save((data.metadata.nombre || "documento") + ".pdf");
    const nombreArchivo = generarNombreArchivo(pagina, cab, data.metadata);
    doc.save(nombreArchivo + ".pdf");
}

// ======================================================
// SEGMENTO (FIX COMPLETO)
// ======================================================

function renderSegmento(doc, seg, cab, baseY) {

    let maxY = baseY;

    // ======================================================
    // ETIQUETAS
    // ======================================================

    (seg.etiquetas || []).forEach(e => {

        let x = parseFloat(e.x);
        let y = baseY + parseFloat(e.y);

        maxY = Math.max(maxY, y);

        doc.setFontSize(parseFloat(e.tamano || 10));

        const align = (e.orientacion || "izquierda") === "derecha"
            ? "right"
            : "left";

        doc.text(e.valor || "", x, y, { align });
    });

    // ======================================================
    // GRAFICOS
    // ======================================================

    (seg.graficos || []).forEach(g => {

        let x = parseFloat(g.x);
        let y = baseY + parseFloat(g.y);

        let ancho = parseFloat(g.ancho || 0);
        let alto = parseFloat(g.alto || 0);

        maxY = Math.max(maxY, y + alto);

        if (g.tipo === "logo") {

            const logo = document.getElementById("company-logo");

            if (logo && logo.dataset.logoLoaded === "true") {
                const base64 = getBase64ImagePdf(logo);
                if (base64) {
                    doc.addImage(base64, "PNG", x, y, ancho, alto);
                }
            } else {
                console.warn("Logo no disponible o no cargado");
            }
        }
        else {

            let [r, gColor, b] = (g.rgb || "0,0,0")
                .split(",")
                .map(v => parseFloat(v));

            doc.setFillColor(r, gColor, b);

            if (g.tipo === "cuadrado") {
                doc.rect(x, y, ancho, alto, "F");
            }
            else if (g.tipo === "cuadrado_cir") {
                doc.roundedRect(x, y, ancho, alto, 0.3, 0.3, "FD");
            }

            doc.setFillColor(0, 0, 0);
        }
    });

    // ======================================================
    // CAMPOS
    // ======================================================

    (seg.campos || []).forEach(c => {

        let valor = devolver_valor_imp(cab[c.campo], c.tipo, c.formato);

        let x = parseFloat(c.x);
        let y = baseY + parseFloat(c.y);

        doc.setFontSize(parseFloat(c.tamano || 10));

        if (c.tipo === "Imagen") {

            let img = document.getElementById(`preview_${c.campo}`);
            if (img && img.src) {
                let base64 = getBase64ImagePdf(img);
                let w = parseFloat(c.largoMaximo || 1);
                let h = parseFloat(c.filasMaximas || 1);
                doc.addImage(base64, "PNG", x, y, w, h);

                maxY = Math.max(maxY, y + h);
            }
        }
        else {
            const lines = obtenerLineasTexto(
                doc,
                valor,
                c.largoMaximo,
                c.filasMaximas
            );

            const align = (c.orientacion || "izquierda") === "derecha"
                ? "right"
                : "left";

            doc.text(lines, x, y, { align });

            const alturaTexto = calcularAlturaTexto(doc,lines,parseFloat(c.tamano || 10));
            maxY = Math.max(maxY, y + alturaTexto);
        }
    });

    return (maxY - baseY) + 0.5;
}

// ======================================================
// UTIL
// ======================================================

// ======================================================
// UTIL
// ======================================================

function estimarAlturaSegmento(seg) {
    let max = 0;

    // =====================================
    // ETIQUETAS
    // =====================================

    (seg.etiquetas || []).forEach(e => {
        max = Math.max(max,parseFloat(e.y || 0));
    });

    // =====================================
    // GRAFICOS
    // =====================================

    (seg.graficos || []).forEach(g => {
        const y = parseFloat(g.y || 0);
        const alto = parseFloat(g.alto || 0);

        max = Math.max(max,y + alto);
    });

    // =====================================
    // CAMPOS
    // =====================================

    (seg.campos || []).forEach(c => {

        let y = parseFloat(c.y || 0);

        // si es imagen puede ocupar más altura
        if (c.tipo === "Imagen") {
            let h = parseFloat(c.filasMaximas || 0);
            max = Math.max(max, y + h);
        }
        else {
            max = Math.max(max, y);
        }
    });

    return max + 0.5;
}

// ======================================================
// UTILIDADES
// ======================================================

function devolver_valor_imp(valor, tipo, formato) {

    if (valor === null || valor === undefined) {
        return "";
    }

    switch (tipo) {

        // ======================================================
        // FECHA
        // ======================================================

        case "Fecha": {

            const date = new Date(valor);

            if (isNaN(date.getTime())) {
                return valor.toString();
            }

            const d = String(date.getDate()).padStart(2, "0");
            const m = String(date.getMonth() + 1).padStart(2, "0");
            const y = date.getFullYear();

            const meses = [
                "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
            ];

            switch (formato) {

                case "Dia":
                    return d;

                case "Mes":
                    return m;

                case "Anio":
                    return y.toString();

                case "DDMMAAAA":
                    return `${d}${m}${y}`;

                case "Cheque":
                    return `${d}/${m}/${y}`;

                case "Letras":
                    return `${y} ${meses[m - 1]} ${d}`;

                case "Letras_larga":
                    return `${d} de ${meses[m - 1]} del ${y}`;

                case "LetrasMayusculas":
                    return `${y} ${meses[m - 1].toUpperCase()} ${d}`;

                case "Normal":
                default:
                    return `${d}/${m}/${y}`;
            }
        }

        // ======================================================
        // NUMERO
        // ======================================================

        case "Numero": {

            const num = parseFloat(valor);

            if (isNaN(num)) {
                return valor.toString();
            }

            switch (formato) {

                case "Miles":
                    return num.toLocaleString("es-ES");

                case "Dolar":
                    return "$ " + num.toLocaleString("es-ES");

                case "Euro":
                    return "€ " + num.toLocaleString("es-ES");

                case "Porcentaje":
                    return (num / 100) + "%";

                case "Porcentaje_full":
                    return num + "%";

                case "Numero":
                default:
                    return num.toString();
            }
        }

        // ======================================================
        // CEROS FIJOS
        // ======================================================

        case "CerosFijos": {

            const texto = valor.toString().trim();
            const minDigitos = parseInt(formato || 0);

            if (!minDigitos || isNaN(minDigitos)) {
                return texto;
            }

            return texto.padStart(minDigitos, "0");
        }

        // ======================================================
        // TEXTO / IMAGEN / DEFAULT
        // ======================================================

        case "Texto":
        case "Imagen":
        default:
            return valor.toString();
    }
}


// Funcion para obtener la imagen en base64 con un tamaño maximo manteniendo la proporcion
function getBase64ImagePdf(img, maxWH = 480, opacity = 1) {
    /* Descripción: Funcion para obtener la imagen en base64 con un tamaño maximo manteniendo la proporcion
     Parametros:
     - img: Imagen a convertir
     - maxWH: Tamaño maximo en pixeles (por defecto 480 si no se especifica)
     
     Retorno: Imagen en base64
    */
    // Create an empty canvas element
    var canvas = document.createElement("canvas");
    // Validar si la imagen es menor al tamaño maximo y ajustar el tamaño del canvas
    if (img.width <= maxWH && img.height <= maxWH) {
        // Si el alto y ancho de la img original es menor al tamaño maximo
        canvas.width = img.width;
        canvas.height = img.height;
    } else if (img.width > img.height) {
        // Else si el ancho es mayor que el alto
        canvas.width = maxWH;
        canvas.height = (img.height * maxWH) / img.width;
    } else if (img.width < img.height) {
        // Else si el alto es mayor que el ancho
        canvas.height = maxWH;
        canvas.width = (img.width * maxWH) / img.height;
    } else {
        // Else si el alto y ancho son iguales
        canvas.width = maxWH;
        canvas.height = maxWH;
    }


    var ctx = canvas.getContext("2d");
    try {
        ctx.globalAlpha = opacity;
        ctx.drawImage(img, 0, 0, img.naturalWidth, img.naturalHeight, 0, 0, canvas.width, canvas.height);
        var dataURL = canvas.toDataURL("image/png");
        return dataURL;
    }
    catch (error) {
        return 0;
    }
}

// Función para dividir un texto en líneas según el ancho máximo permitido, considerando palabras y caracteres
function obtenerLineasTexto(doc, texto, largoMaximo, filasMaximas = null) {

    texto = texto.toString();

    if (!largoMaximo) return [texto];

    const maxWidth = parseFloat(largoMaximo);

    const words = texto.split(" ");
    let lines = [];
    let currentLine = "";

    words.forEach(word => {

        let testLine = currentLine ? currentLine + " " + word : word;

        // 🔹 Si cabe, seguimos normal
        if (doc.getTextWidth(testLine) <= maxWidth) {
            currentLine = testLine;
        } else {

            // 🔥 Si la palabra sola es demasiado grande → dividir por caracteres
            if (doc.getTextWidth(word) > maxWidth) {

                let subWord = "";

                for (let char of word) {

                    let testSub = subWord + char;

                    if (doc.getTextWidth(testSub) > maxWidth) {
                        if (subWord) lines.push(subWord);
                        subWord = char;
                    } else {
                        subWord = testSub;
                    }
                }

                if (subWord) {
                    currentLine = subWord;
                } else {
                    currentLine = "";
                }

            } else {

                if (currentLine) lines.push(currentLine);
                currentLine = word;
            }
        }
    });

    if (currentLine) lines.push(currentLine);

    if (filasMaximas) {
        lines = lines.slice(0, parseInt(filasMaximas));
    }

    return lines;
}

// Función para calcular la altura total de un bloque de texto dado el número de líneas y el tamaño de fuente, estimando el interlineado
function calcularAlturaTexto(doc, lines, fontSize) {
    const lineHeightFactor = doc.getLineHeightFactor();
    const alturaLinea = (fontSize / doc.internal.scaleFactor) * lineHeightFactor;
    return lines.length * alturaLinea;
}

// Función para generar un nombre de archivo dinámco basado en pagina.formatNombre (nuevo esquema array)
function generarNombreArchivo(pagina, cab, metadata) {

    const format = pagina.formatNombre;
    const now = new Date();

    const getFechaHora = () => {
        const fecha = now.toLocaleDateString();
        const hora = now.toLocaleTimeString().replace(/:/g, "-");
        return `${fecha}_${hora}`;
    };

    let nombre = "documento";

    // ======================================================
    // SIN FORMATO DEFINIDO
    // ======================================================

    if (
        !format ||
        format === "No" ||
        (Array.isArray(format) && format.length === 0)
    ) {
        const base = cab["Descripcion"] || metadata.nombre || "documento";
        nombre = `${base}_${getFechaHora()}`;
    }

    // ======================================================
    // NUEVO FORMATO ARRAY
    // ======================================================

    else {

        // Seguridad por compatibilidad:
        // si aún llega string viejo, lo convertimos
        const campos = Array.isArray(format)
            ? format
            : format.toString().split(",");

        let valores = [];

        campos.forEach(campo => {
            const val = cab[campo];

            if (
                val !== undefined &&
                val !== null &&
                val !== ""
            ) {
                valores.push(val.toString());
            }
        });

        const base = cab["Descripcion"] || metadata.nombre || "documento";

        if (valores.length) {
            nombre = `${base}_${valores.join("_")}`;
        } else {
            nombre = `${base}_${getFechaHora()}`;
        }
    }

    return nombre.replace(/[\/\\:*?"<>|]/g, "_");
}