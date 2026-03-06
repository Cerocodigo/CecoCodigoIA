async function generatePdfReport(report_data, incluirSubniveles = true) {

    const { jsPDF } = window.jspdf;

    const pdfConfig = report_data.exportacion_config.pdf;
    if (incluirSubniveles && pdfConfig.length === 1) {
        incluirSubniveles = false;
    }

    const orientacionConfig = pdfConfig.find(c => c.Nivel === 0)?.Posicion || "Vertical";

    const orientation =
        orientacionConfig.toLowerCase() === "horizontal"
            ? "landscape"
            : "portrait";

    const doc = new jsPDF({
        orientation: orientation,
        unit: "pt",
        format: "a4"
    });

    const FONT_SIZE_BODY = 8;
    const FONT_SIZE_HEADER = 9;

    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();

    const marginLeft = 40;
    const marginRight = 40;

    const HEADER_HEIGHT = 55;
    const marginTop = HEADER_HEIGHT + 20;

    let y = marginTop;

    const nivelesConfig = report_data.niveles_config;
    const data = report_data.resultado_niveles;

    const printableWidth = pageWidth - marginLeft - marginRight;

    let lastHeader = null;

    const nombreAutor = window.APP?.user?.firstName || "Owner";

    const fechaGeneracion = new Date().toLocaleString();

    function drawPageHeader() {

        const title = report_data.meta.nombre;
        const reportParams = collectParametros();

        const varsText = Object.entries(reportParams)
            .map(([key, value]) => `${key}: ${value}`)
            .join(" | ");

        const leftX = pageWidth * 0.30;
        const rightX = pageWidth - marginRight;

        let headerY = 25;

        doc.setFont("helvetica", "bold");
        doc.setFontSize(8);

        doc.text(title, leftX, headerY);

        doc.setFont("helvetica", "normal");
        doc.setFontSize(8);

        doc.text(
            `${nombreAutor} - ${fechaGeneracion}`,
            rightX,
            headerY,
            { align: "right" }
        );

        headerY += 4;

        const lineStart = pageWidth * 0.30;
        const lineEnd = pageWidth - marginRight;

        doc.setDrawColor(0, 102, 204);
        doc.setLineWidth(1);

        doc.line(lineStart, headerY, lineEnd, headerY);

        headerY += 8;

        doc.setFontSize(8);
        doc.setFont("helvetica", "normal");

        doc.text(varsText, leftX, headerY);
        doc.setLineWidth(0.5);
    }

    drawPageHeader();

    function pageBreakIfNeeded(height = 20) {

        if (y + height > pageHeight - 40) {

            doc.addPage();

            drawPageHeader();

            y = marginTop;

            if (lastHeader)
                drawRow(lastHeader.values, lastHeader.conf, lastHeader.cols, lastHeader.widths, true);
        }
    }

    function parseColumns(conf, nivel) {

        if (conf.ColumnasMostrar === "*")
            return nivelesConfig[nivel].columnas;

        return conf.ColumnasMostrar.split(",").map(c => c.trim());
    }

    function parseWidths(conf, cols) {

        const tab = conf.TabNivel || 0;

        const usableWidth = printableWidth - tab;

        if (conf.Largos === "*") {

            const w = usableWidth / cols.length;
            return cols.map(() => w);
        }

        const raw = conf.Largos.split(",").map(n => Number(n.trim()));
        const total = raw.reduce((a, b) => a + b, 0);

        return raw.map(v => usableWidth * (v / total));
    }

    function drawCell(text, x, y, w, h, border) {

        const padding = 4;

        const lines = doc.splitTextToSize(
            String(text ?? ""),
            w - padding * 2
        );

        if (border)
            doc.rect(x, y - h + padding, w, h);

        doc.text(
            lines,
            x + padding,
            y,
            { maxWidth: w - padding * 2 }
        );

        return lines.length;
    }

    function drawRow(rowValues, conf, cols, widths, isHeader = false) {

        const tab = conf.TabNivel || 0;
        const border = conf.Lineas === true;

        const padding = 4;
        const lineHeight = 10;

        let x = marginLeft + tab;

        const linesPerCell = [];

        for (let i = 0; i < cols.length; i++) {

            const txt = String(rowValues[i] ?? "");

            const lines = doc.splitTextToSize(
                txt,
                widths[i] - padding * 2
            );

            linesPerCell.push(lines);
        }

        const maxLines = Math.max(...linesPerCell.map(l => l.length));

        const h = maxLines * lineHeight + padding * 2;

        pageBreakIfNeeded(h);

        const rowTop = y;

        if (isHeader) {

            const color = conf.Colores?.cabecera || [240, 240, 240];

            doc.setFillColor(...color);

            let hx = marginLeft + tab;

            widths.forEach(w => {

                doc.rect(hx, rowTop, w, h, "F");

                hx += w;

            });

            doc.setFont("helvetica", "bold");
            doc.setFontSize(FONT_SIZE_HEADER);

            lastHeader = { values: rowValues, conf, cols, widths };

        } else {

            doc.setFont("helvetica", "normal");
            doc.setFontSize(FONT_SIZE_BODY);
        }

        for (let i = 0; i < cols.length; i++) {

            const lines = linesPerCell[i];

            if (border)
                doc.rect(x, rowTop, widths[i], h);

            doc.text(
                lines,
                x + padding,
                rowTop + padding + lineHeight
            );

            x += widths[i];
        }

        y += h;
    }

    function renderLevel(level, rows) {

        const conf = pdfConfig.find(c => c.Nivel === level);
        if (!conf) return;

        const nivelDef = nivelesConfig[level];

        const cols = parseColumns(conf, level);
        const widths = parseWidths(conf, cols);

        if (conf.MostrarCabecera)
            drawRow(cols, conf, cols, widths, true);

        let totals = {};

        rows.forEach(row => {

            pageBreakIfNeeded();

            drawRow(cols.map(c => row[c]), conf, cols, widths);

            if (nivelDef.totales?.length) {

                nivelDef.totales.forEach(t => {

                    totals[t.columna] =
                        (totals[t.columna] || 0) + Number(row[t.columna] || 0);

                });
            }

            if (!incluirSubniveles)
                return;

            const nextLevel = level + 1;

            const nextNivelDef = nivelesConfig[nextLevel];
            if (!nextNivelDef)
                return;

            const parentField = nextNivelDef.vinculos?.campo_padre;
            if (!parentField)
                return;

            const children = data[String(nextLevel)]?.[row[parentField]] || [];

            if (!children.length)
                return;

            y += 8;

            renderLevel(nextLevel, children);

        });

        if (nivelDef.totales?.length) {

            const rowTot = cols.map(() => "");

            nivelDef.totales.forEach(t => {

                const idx = cols.indexOf(t.columna);

                if (idx >= 0)
                    rowTot[idx] = (totals[t.columna] || 0).toFixed(2);

            });

            rowTot[Math.max(cols.length - 3, 0)] = "TOTAL";

            drawRow(rowTot, conf, cols, widths, true);
        }

        y += 12;
    }

    const nivel0 = data["0"] || [];

    renderLevel(0, nivel0);

    doc.save(report_data.meta.id + ".pdf");
}