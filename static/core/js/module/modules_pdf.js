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

            if (el.type === "checkbox") data[el.name] = el.checked;
            else if (el.type === "radio") {
                if (el.checked) data[el.name] = el.value;
            } else data[el.name] = el.value;
        });
    });

    return [data];
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

    const cab = data.valores_cab[0];
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

            const registros = det[seg.modelo_id];
            if (!registros) return;

            y += parseFloat(seg.alturaInicial || 0);

            doc.setFont(undefined, "bold");
            seg.columnas.forEach(col => {
                if (col.tipo === "Derecha") {
                    doc.text(parseFloat(col.x), y, col.cabecera, { align: "right" });
                }
                else if (col.tipo === "Centro") {
                        let x = parseFloat(col.x);
                        let w = parseFloat(col.largoMaximo || 0);
                        doc.text(x + (w / 2), y, col.cabecera, { align: "center" });
                }
                else {
                    doc.text(parseFloat(col.x), y, col.cabecera);
                }
            });

            doc.setFont(undefined, "normal");
            y += 0.5;

            registros.forEach((row, i) => {

                let alturaFila = 0.5;

                seg.columnas.forEach(col => {
                    let valor = devolver_valor_imp(row[col.campo], col.tipo, col.ext);
                    doc.setFontSize(parseFloat(col.tamano || 8));
                    let x = parseFloat(col.x);
                    if (col.tipo === "Imagen") {
                        let img = document.getElementById(`preview_${col.campo}`);
                        if (img && img.src) {
                            let base64 = getBase64ImagePdf(img);
                            let w = parseFloat(col.largoMaximo || 1);
                            let h = parseFloat(col.filasMaximas || 1);
                            doc.addImage(base64, "PNG", x, y, w, h);
                            alturaFila = Math.max(alturaFila, h);
                        }
                    }
                    else {
                        const lines = obtenerLineasTexto(
                            doc,
                            valor,
                            col.largoMaximo,
                            null // 🔥 detalle NO limita filas (por ahora)
                        );
                        if (col.tipo === "Derecha") {
                            doc.text(lines, x, y, { align: "right" });
                        }
                        else if (col.tipo === "Centro") {
                            let w = parseFloat(col.largoMaximo || 0);
                            doc.text(lines, x + (w / 2), y, { align: "center" });
                        }
                        else {
                            doc.text(lines, x, y);
                        }
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

    (seg.etiquetas || []).forEach(e => {

        let x = parseFloat(e.x);
        let y = baseY + parseFloat(e.y);

        maxY = Math.max(maxY, y);

        if (e.tipo === "Logo") {
            const logo = document.getElementById("company-logo");

            // ✅ Solo usar si realmente cargó
            if (logo && logo.dataset.logoLoaded === "true") {
                const base64 = getBase64ImagePdf(logo);
                if (base64) {
                    let [w, h] = e.tamano.split(",").map(parseFloat);
                    doc.addImage(base64, "PNG", x, y, w, h);
                }
            } else {
                // ❌ No hay logo usable → puedes ignorar o usar fallback
                console.warn("Logo no disponible o no cargado");
            }



        }

        else {
            doc.setFontSize(parseFloat(e.tamano || 10));
            doc.text(x, y, e.valor);
        }
    });
    // ======================================================
    // GRAFICOS (nuevo esquema separado de etiquetas)
    // ======================================================

    (seg.grafico || []).forEach(g => {

        let x = parseFloat(g.x);
        let y = baseY + parseFloat(g.y);

        let ancho = parseFloat(g.ancho || 0);
        let alto = parseFloat(g.alto || 0);

        maxY = Math.max(maxY, y + alto);

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
    });


    (seg.campos || []).forEach(c => {

        let valor = devolver_valor_imp(cab[c.campo], c.tipo, c.ext);

        let x = parseFloat(c.x);
        let y = baseY + parseFloat(c.y);

        doc.setFontSize(parseFloat(c.tamano || 10));

        if (c.tipo === "Color") {
            let [r, g, b, size] = c.ext.split(",");
            doc.setTextColor(r, g, b);
            doc.setFontSize(size);
            doc.text(x, y, valor);
            doc.setTextColor(0, 0, 0);
        }

        else if (c.tipo === "Barras") {
            let svg = document.createElement("svg");
            JsBarcode(svg, valor);

            let canvas = document.createElement("canvas");
            canvg(canvas, svg.outerHTML);

            let img = canvas.toDataURL("image/png");

            // let [w, h] = c.limite.split(",");
            let w = parseFloat(c.largoMaximo || 3);
            let h = parseFloat(c.filasMaximas || 1);
            doc.addImage(img, "PNG", x, y, w, h);
        }

        else {
            const lines = obtenerLineasTexto(
                doc,
                valor,
                c.largoMaximo,
                c.filasMaximas
            );

            if (c.tipo === "Derecha") {
                doc.text(lines, x, y, { align: "right" });
            }
            else if (c.tipo === "Centro") {
                let w = parseFloat(c.largoMaximo || 0);
                doc.text(lines, x + (w / 2), y, { align: "center" });
            }
            else {
                doc.text(lines, x, y);
            }

            // 🔥 actualizar altura real
            const alturaTexto = lines.length * 0.4;
            maxY = Math.max(maxY, y + alturaTexto);
        }
    });

    return (maxY - baseY) + 0.5;
}

// ======================================================
// UTIL
// ======================================================

function estimarAlturaSegmento(seg) {
    let max = 0;

    (seg.etiquetas || []).forEach(e => {
        max = Math.max(max, parseFloat(e.y || 0));
    });

    (seg.grafico || []).forEach(g => {
        const y = parseFloat(g.y || 0);
        const alto = parseFloat(g.alto || 0);
        max = Math.max(max, y + alto);
    });

    (seg.campos || []).forEach(c => {
        max = Math.max(max, parseFloat(c.y || 0));
    });

    return max + 0.5;
}

// ======================================================
// UTILIDADES
// ======================================================

function devolver_valor_imp(valor, tipo, ext) {

    if (valor === null || valor === undefined) {
        return "";
    }

    switch (tipo) {

        case "Fecha":

            const date = new Date(valor);

            const d = String(date.getDate()).padStart(2, "0");
            const m = String(date.getMonth() + 1).padStart(2, "0");
            const y = date.getFullYear();

            const meses = [
                "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
            ];

            switch (ext) {

                case "Dia": return d;
                case "Mes": return m;
                case "Anio": return y;

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

                default:
                    return `${d}/${m}/${y}`;
            }


        case "Numero":
        case "Derecha":

            const num = parseFloat(valor);

            if (isNaN(num)) return valor.toString();

            switch (ext) {

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

                default:
                    return num.toString();
            }

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
        return 0
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


// Función para generar un nombre de archivo dinámico basado en un formato definido, utilizando valores de cabecera y metadata
function generarNombreArchivo(pagina, cab, metadata) {
    const format = pagina.formatNombre;
    const now = new Date();

    const getFechaHora = () => {
        const fecha = now.toLocaleDateString();
        const hora = now.toLocaleTimeString().replace(/:/g, "-");
        return `${fecha}_${hora}`;
    };

    let nombre = "documento";
    if (!format || format === "No") {
        const base = cab["Descripcion"] || metadata.nombre || "documento";
        nombre = `${base}_${getFechaHora()}`;
    }
    else {
        const campos = format.toString().split(",");
        let valores = [];

        campos.forEach(campo => {
            const val = cab[campo];
            if (val !== undefined && val !== null && val !== "") {
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