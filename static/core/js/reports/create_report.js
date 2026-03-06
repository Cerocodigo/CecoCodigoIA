// static/core/js/reports/create_report.js
// ==================================================
// Manejo frontend para generación de reportes IA
// ==================================================

document.addEventListener("DOMContentLoaded", function () {

    const promptTextarea = document.getElementById("reportPrompt");
    const generateBtn = document.getElementById("generateReportBtn");
    const loadingIndicator = document.getElementById("report-loading");
    const previewContainer = document.getElementById("reportPreviewContainer");

    if (!promptTextarea || !generateBtn) {
        return;
    }


    // ================================================
    // UI helpers
    // ================================================
    function setLoading(isLoading) {
        if (isLoading) {
            loadingIndicator.style.display = "block";
            generateBtn.disabled = true;
            promptTextarea.disabled = true;
        } else {
            loadingIndicator.style.display = "none";
            generateBtn.disabled = false;
            promptTextarea.disabled = false;
        }
    }

    function renderError(message, details = []) {

        let html = `
            <div class="alert alert-danger">
                <strong>${message}</strong>
        `;

        if (details && details.length > 0) {
            html += "<ul class='mt-2 mb-0'>";
            for (let err of details) {
                html += `<li>${err}</li>`;
            }
            html += "</ul>";
        }

        html += "</div>";

        previewContainer.innerHTML = html;
    }

    function renderSuccess(report) {

        let html = `
            <div class="alert alert-success">
                <strong>Reporte generado correctamente</strong>
            </div>

            <div class="card border-left-primary shadow mb-4">
                <div class="card-body">
                    <h5 class="font-weight-bold">${report.nombre}</h5>
                    <p class="mb-2 text-muted">${report.descripcion}</p>

                    <div class="mb-2">
                        <strong>Módulos:</strong>
                        ${report.modulos.join(", ")}
                    </div>

                    <div class="mb-2">
                        <strong>Exportable:</strong>
                        PDF: ${report.exportable.pdf ? "Sí" : "No"} |
                        Excel: ${report.exportable.excel ? "Sí" : "No"}
                    </div>

                    <div>
                        <strong>Versión:</strong> ${report.version}
                    </div>
                </div>
            </div>
        `;

        previewContainer.innerHTML = html;
    }

    // ================================================
    // Llamada API
    // ================================================
    async function generateReport() {

        const prompt = promptTextarea.value.trim();

        if (!prompt) {
            renderError("Debes escribir una instrucción para generar el reporte.");
            return;
        }

        setLoading(true);

        try {

            const response = await fetch("/reports/api/create/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCSRFToken(),
                },
                body: JSON.stringify({
                    prompt: prompt,
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                renderError(
                    data.error || "Error al generar el reporte.",
                    data.details || []
                );
                return;
            }

            if (data.success) {
                renderSuccess(data.report);
            } else {
                renderError(
                    "No fue posible generar el reporte.",
                    data.details || []
                );
            }

        } catch (error) {
            renderError("Error de conexión con el servidor.");
        } finally {
            setLoading(false);
        }
    }

    // ================================================
    // Eventos
    // ================================================
    generateBtn.addEventListener("click", function () {
        generateReport();
    });

    promptTextarea.addEventListener("keydown", function (e) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            generateReport();
        }
    });

});