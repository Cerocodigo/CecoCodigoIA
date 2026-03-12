// static/core/js/reports/create_excel_report.js

// ==========================================
// CONFIGURACIONES BASE
// ==========================================

const EXCEL_FORMATS = {
    textGeneral: null,
    numberGeneral: null,
    date: 'yyyy-mm-dd',
    dateTime: 'yyyy-mm-dd hh:mm',
    number2Decimals: '#,##0.00',
    number6Decimals: '#,##0.000000'
};

// ==========================================
// FUNCIÓN PRINCIPAL
// ==========================================

async function generateExcelReport(reporte, incluirSubniveles) {

    const workbook = new ExcelJS.Workbook();
    const sheet = workbook.addWorksheet(reporte.meta.nombre);

    let currentRow = 1;

    // ==========================
    // 1. Obtener configuración Excel
    // ==========================

    const excelConfig = reporte.exportacion_config?.excel || [];

    // ==========================
    // 2. Metadata del reporte
    // ==========================

    // currentRow = writeReportHeader(sheet, reporte, currentRow, excelConfig);
    currentRow = writeReportHeader(sheet, reporte, currentRow, excelConfig, incluirSubniveles);

    currentRow += 1;

    // ==========================
    // 3. Render niveles
    // ==========================

    currentRow = await renderExcelNivel(sheet,reporte,excelConfig,0,null,currentRow,incluirSubniveles);

    // ==========================
    // 4. Ajuste automático columnas
    // ==========================

    autoFitColumns(sheet);

    // ==========================
    // 5. Descargar archivo
    // ==========================

    const buffer = await workbook.xlsx.writeBuffer();

    const blob = new Blob([buffer], {
        type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    });

    const url = window.URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = `${reporte.meta.nombre}.xlsx`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    window.URL.revokeObjectURL(url);
}


// function writeReportHeader(sheet, reporte, row, excelConfig) {
function writeReportHeader(sheet, reporte, row, excelConfig, incluirSubniveles) {

    const nivel0Config = excelConfig[0] || {};
    const tab = nivel0Config?.TabNivel || 0;

    const startCol = tab + 1;
    const endCol = getRealColumnSpan(reporte,excelConfig,incluirSubniveles);

    const parametros = collectParametros();

    const now = new Date();
    const formattedNow =
        now.toLocaleDateString('es-ES') + " " +
        now.toLocaleTimeString('es-ES');

    const nombreAutor =
    window.APP?.user?.firstName || "Owner";


    const headerLines = [
        reporte.meta.nombre,
        reporte.meta.descripcion,
        `Generado por: ${nombreAutor} ${formattedNow}`,
        ...Object.entries(parametros).map(([k, v]) => `${k}: ${v}`)
    ];

    headerLines.forEach((text, index) => {

        const rowObj = sheet.getRow(row);

        sheet.mergeCells(row, startCol, row, endCol);

        const cell = sheet.getCell(row, startCol);
        cell.value = text;

        cell.font = {
            bold: true,
            size: index === 0 ? 14 : 11
        };

        cell.alignment = {
            horizontal: "center",
            vertical: "middle"
        };

        applyBorderRange(sheet, row, startCol, row, endCol);

        row++;
    });

    return row + 1; // fila vacía después del header
}

async function renderExcelNivel(sheet, reporte, excelConfig, nivel, parentKey, row, incluirSubniveles) {

    const nivelConfig = reporte.niveles_config[nivel];
    const exportConfig = excelConfig.find(e => e.Nivel === nivel);

    if (!nivelConfig || !exportConfig) return row;

    const columnas = resolveColumnas(nivelConfig, exportConfig);
    const tipos = resolveTipos(columnas, exportConfig);

    const tab = exportConfig.TabNivel || 0;
    const conCabecera = exportConfig.ConCabecera === "Si";

    const data = resolveDataNivel(reporte, nivel, parentKey);

    if (!data.length) return row;

    // -------------------------
    // Cabecera
    // -------------------------

    if (conCabecera) {

        let colIndex = tab + 1;

        columnas.forEach(col => {

            const cell = sheet.getCell(row, colIndex++);
            cell.value = col;
            cell.font = { bold: true };

        });
        applyBorderRange(sheet, row, tab + 1, row, tab + columnas.length);

        row++;
    }

    // -------------------------
    // Filas
    // -------------------------

    for (const item of data) {

        let colIndex = tab + 1;

        columnas.forEach((col, index) => {
            const cell = sheet.getCell(row, colIndex++);
            applyCellValue(cell, item[col], tipos[index]);
        });

        applyBorderRange(sheet, row, tab + 1, row, tab + columnas.length);

        row++;

        if (incluirSubniveles) {

            const vinculo = nivelConfig.vinculos?.campo_hijo;

            if (vinculo && reporte.niveles_config[nivel + 1]) {

                const childData = resolveDataNivel(
                    reporte,
                    nivel + 1,
                    item[vinculo]
                );

                if (childData.length > 0) {

                    row++; // fila vacía antes del detalle

                    row = await renderExcelNivel(
                        sheet,
                        reporte,
                        excelConfig,
                        nivel + 1,
                        item[vinculo],
                        row,
                        incluirSubniveles
                    );

                    row++; // fila vacía después del detalle
                }
            }
        }
    }

    // -------------------------
    // Totales
    // -------------------------

    if (nivelConfig.totales?.length) {

        row = renderTotales(
            sheet,
            data,
            columnas,
            nivelConfig.totales,
            tipos,
            tab,
            row
        );
    }

    return row;
}


function resolveColumnas(nivelConfig, exportConfig) {

    if (exportConfig.ColumnasMostrar === "*") {
        return nivelConfig.columnas;
    }

    return exportConfig.ColumnasMostrar.split(", ").map(c => c.trim());
}



function resolveTipos(columnas, exportConfig) {

    if (exportConfig.TipoDatoColumnas === "*") {

        return columnas.map(col => inferType(col));
    }

    return exportConfig.TipoDatoColumnas.split(", ").map(t => t.trim());
}


function inferType(col) {

    if (col.toLowerCase().includes("fecha")) return "date";
    if (col.toLowerCase().includes("debe")) return "number2Decimals";
    if (col.toLowerCase().includes("haber")) return "number2Decimals";
    if (col.toLowerCase().includes("total")) return "number2Decimals";

    return "textGeneral";
}


function applyCellValue(cell, value, tipo) {
    if (value === null || value === undefined) {
        cell.value = "";
        return;
    }

    switch (tipo) {
        case "date":
            cell.value = new Date(value);
            cell.numFmt = EXCEL_FORMATS.date;
            break;

        case "dateTime":
            cell.value = new Date(value);
            cell.numFmt = EXCEL_FORMATS.dateTime;
            break;

        case "number2Decimals":
            cell.value = parseFloat(value);
            cell.numFmt = EXCEL_FORMATS.number2Decimals;
            break;

        case "number6Decimals":
            cell.value = parseFloat(value);
            cell.numFmt = EXCEL_FORMATS.number6Decimals;
            break;

        case "numberGeneral":
            cell.value = parseFloat(value);
            break;

        default:
            cell.value = value.toString();
    }
}


function renderTotales(
    sheet,
    data,
    columnas,
    totalesConfig,
    tipos,
    tab,
    row
) {

    let colIndex = tab + 1;

    columnas.forEach((col, index) => {

        const totalConfig = totalesConfig.find(t => t.columna === col);

        const cell = sheet.getCell(row, colIndex++);

        if (totalConfig && totalConfig.tipo === "SUM") {

            const total = data.reduce((acc, item) => {
                return acc + (parseFloat(item[col]) || 0);
            }, 0);

            applyCellValue(cell, total, tipos[index]);
            cell.font = { bold: true };

        } else {
            cell.value = "";
        }
    });
    applyBorderRange(sheet, row, tab + 1, row, tab + columnas.length);

    return row + 1;
}


function resolveDataNivel(reporte, nivel, parentKey) {

    const result = reporte.resultado_niveles[nivel];

    if (nivel === 0) return result || [];

    return result?.[String(parentKey)] || [];
}


function autoFitColumns(sheet) {

    sheet.columns.forEach(column => {

        let maxLength = 8;

        column.eachCell({ includeEmpty: false }, cell => {

            // 👇 Ignorar celdas combinadas
            if (cell.isMerged) return;

            const value = cell.value;

            if (!value) return;

            const length = value.toString().length;

            if (length > maxLength) maxLength = length;
        });

        column.width = Math.min(maxLength + 2, 40); // 👈 límite máximo
    });
}


function getRealColumnSpan(reporte, excelConfig, incluirSubniveles) {

    let max = 0;

    excelConfig.forEach(cfg => {

        // 👇 Si NO se incluyen subniveles, solo nivel 0
        if (!incluirSubniveles && cfg.Nivel !== 0) return;

        const nivelConfig = reporte.niveles_config[cfg.Nivel];
        if (!nivelConfig) return;

        const columnas = resolveColumnas(nivelConfig, cfg);
        const span = (cfg.TabNivel || 0) + columnas.length;

        if (span > max) max = span;
    });

    return max;
}


function applyBorderRange(sheet, rowStart, colStart, rowEnd, colEnd) {

    for (let r = rowStart; r <= rowEnd; r++) {
        for (let c = colStart; c <= colEnd; c++) {

            const cell = sheet.getCell(r, c);

            cell.border = {
                top: { style: 'thin' },
                left: { style: 'thin' },
                bottom: { style: 'thin' },
                right: { style: 'thin' }
            };
        }
    }
}

