// static/core/js/plantillas_prehecho/aplicar_plantilla_prehecho.js

document.addEventListener("DOMContentLoaded", () => {
    // =========================
    // DOM
    // =========================
    const analysisContainer = document.getElementById(
        "analysis-container"
    );

    const metadataContainer = document.getElementById(
        "metadata-container"
    );

    const applicationContainer = document.getElementById(
        "application-container"
    );

    const applicationStatusTitle = document.getElementById(
        "application-status-title"
    );

    const applicationStatusDescription = document.getElementById(
        "application-status-description"
    );

    const applicationProgressBar = document.getElementById(
        "application-progress-bar"
    );

    const applicationLogContainer = document.getElementById(
        "application-log-container"
    );

    const strategyContainer = document.getElementById(
        "strategy-container"
    );

    const warningContainer = document.getElementById(
        "warning-container"
    );

    const contentTitle = document.getElementById(
        "content-title"
    );

    const btnContinuar = document.getElementById(
        "btnContinuar"
    );

    const wizardSteps = document.querySelectorAll(
        "#wizard-steps .list-group-item"
    );

    // =========================
    // Obtener plantilla desde URL
    // =========================
    const currentPath = window.location.pathname;

    const pathParts = currentPath
        .split("/")
        .filter(Boolean);

    const plantillaId = pathParts[1];

    if (!plantillaId) {
        analysisContainer.innerHTML = `
            <div class="alert alert-danger">
                No se pudo identificar la plantilla.
            </div>
        `;
        return;
    }

    // =========================
    // Estado global
    // =========================
    let analysisData = null;

    let metadataDefinition = [];

    let currentStep = "analysis";

    // =========================
    // Cambiar título contenido
    // =========================
    function setContentTitle(title) {
        contentTitle.innerText = title;
    }

    // =========================
    // Cambiar paso visual
    // =========================
    function setActiveStep(stepName) {
        wizardSteps.forEach((item) => {
            item.classList.remove(
                "active"
            );
            if (
                item.dataset.step === stepName
            ) {
                item.classList.add("active");
            }
        });
    }

    // =========================
    // Inicializar
    // =========================
    setActiveStep("analysis");
    setContentTitle("Análisis de impacto");

    loadAnalysis();

    // =========================
    // Eventos
    // =========================
    btnContinuar.addEventListener(
        "click",
        onClickContinuar
    );

    // =========================
    // Continuar flujo
    // =========================
    async function onClickContinuar() {

        // =========================
        // Paso análisis
        // =========================
        if (currentStep === "analysis") {

            await startMetadataStep();

            return;
        }

        // =========================
        // Paso metadata
        // =========================
        if (currentStep === "metadata") {
            clearFieldErrors();
            const validation = (
                validateMetadataForm()
            );
            if (!validation.valid) {
                return;
            }
            const formData = (
                collectMetadataFormData()
            );

            const selectedStrategy = document.querySelector(
                'input[name="apply_strategy"]:checked'
            );

            formData.append(
                "strategy",
                selectedStrategy.value
            );
            console.log(
                "Metadata recopilada:",
                formData
            );

            await startApplicationStep(formData);

            return;
        }
    }

    // =========================
    // Iniciar metadata
    // =========================
    async function startMetadataStep() {
        currentStep = "metadata";
        warningContainer.classList.add("d-none");
        setActiveStep("metadata");
        setContentTitle("Pre-configuración de plantilla");

        analysisContainer.classList.add(
            "d-none"
        );

        strategyContainer.classList.add(
            "d-none"
        );

        metadataContainer.classList.remove(
            "d-none"
        );

        metadataContainer.innerHTML = `
            <div class="text-center py-5">

                <div
                    class="spinner-border text-primary mb-3"
                    role="status"
                ></div>

                <p class="text-muted mb-0">
                    Cargando configuración dinámica...
                </p>

            </div>
        `;

        btnContinuar.disabled = true;

        try {

            const response = await fetch(
                `/aplicar-prehecho/${plantillaId}/metadata/`
            );

            const data = await response.json();

            if (!data.success) {

                metadataContainer.innerHTML = `
                    <div class="alert alert-danger">
                        ${data.message || "Error cargando metadata"}
                    </div>
                `;
                currentStep = "analysis";

                setActiveStep("analysis");
                setContentTitle("Análisis de impacto");
                return;
            }

            metadataDefinition = (
                data.metadata || []
            );

            renderMetadataForm();

            btnContinuar.innerText = (
                "Aplicar plantilla"
            );

        } catch (error) {

            console.error(error);

            metadataContainer.innerHTML = `
                <div class="alert alert-danger">
                    Ocurrió un error cargando metadata.
                </div>
            `;

        } finally {

            btnContinuar.disabled = false;
        }
    }

    // =========================
    // Cargar análisis
    // =========================
    async function loadAnalysis() {
        try {
            const response = await fetch(
                `/aplicar-prehecho/${plantillaId}/analysis/`
            );

            const data = await response.json();

            if (!data.success) {

                analysisContainer.innerHTML = `
                    <div class="alert alert-danger">
                        ${data.message || "Error analizando plantilla"}
                    </div>
                `;

                return;
            }

            analysisData = data.analysis;

            renderAnalysis(
                analysisData
            );

            strategyContainer.classList.remove(
                "d-none"
            );

            btnContinuar.disabled = false;

        } catch (error) {

            console.error(error);

            analysisContainer.innerHTML = `
                <div class="alert alert-danger">
                    Ocurrió un error cargando el análisis.
                </div>
            `;
        }
    }

    // =========================
    // Render análisis
    // =========================
    function renderAnalysis(analysis) {

        const tables = analysis.tables || [];

        // =========================
        // Sin tablas
        // =========================
        if (!tables.length) {
            analysisContainer.innerHTML = `
                <div class="alert alert-success mb-0">
                    No existen tablas previas en la empresa.
                </div>
            `;

            strategyContainer.classList.remove(
                "d-none"
            );

            btnContinuar.disabled = false;

            return;
        }

        let rowsHtml = "";

        tables.forEach((table) => {

            const actionBadge = (
                table.exists_in_template
                    ?
                    `
                    <span class="badge badge-warning">
                        Compatible
                    </span>
                `
                    :
                    `
                    <span class="badge badge-danger">
                        Se eliminará
                    </span>
                `
            );

            rowsHtml += `
                <tr>

                    <td>
                        ${table.table_name}
                    </td>

                    <td>
                        ${table.current_records}
                    </td>

                    <td>
                        ${actionBadge}
                    </td>

                </tr>
            `;
        });

        analysisContainer.innerHTML = `
            <div class="table-responsive">

                <table class="table table-bordered">

                    <thead>

                        <tr>

                            <th>
                                Tabla
                            </th>

                            <th>
                                Registros
                            </th>

                            <th>
                                Estado
                            </th>

                        </tr>

                    </thead>

                    <tbody>
                        ${rowsHtml}
                    </tbody>

                </table>

            </div>
        `;
    }

    // =========================
    // Iniciar aplicación
    // =========================
    async function startApplicationStep(formData) {

        currentStep = "application";

        setActiveStep(
            "application"
        );

        setContentTitle(
            "Aplicando plantilla"
        );

        metadataContainer.classList.add(
            "d-none"
        );

        applicationContainer.classList.remove(
            "d-none"
        );

        btnContinuar.disabled = true;

        btnContinuar.innerText = (
            "Aplicando..."
        );

        resetApplicationUI();

        await simulateApplicationProcess(
            formData
        );
    }

    // =========================
    // Reset UI aplicación
    // =========================
    function resetApplicationUI() {

        applicationProgressBar.style.width = (
            "0%"
        );

        applicationProgressBar.innerText = (
            "0%"
        );

        applicationLogContainer.innerHTML = "";

        applicationStatusTitle.innerText = (
            "Preparando aplicación..."
        );

        applicationStatusDescription.innerText = (
            "Inicializando proceso..."
        );
    }

    // =========================
    // Actualizar progreso
    // =========================
    function updateApplicationProgress(
        percent,
        title,
        description
    ) {

        applicationProgressBar.style.width = (
            `${percent}%`
        );

        applicationProgressBar.innerText = (
            `${percent}%`
        );

        applicationStatusTitle.innerText = (
            title
        );

        applicationStatusDescription.innerText = (
            description
        );
    }

    // =========================
    // Añadir log
    // =========================
    function appendApplicationLog(
        message
    ) {

        const row = document.createElement(
            "div"
        );

        row.className = (
            "mb-2"
        );

        row.innerHTML = `
        <small>
            ${message}
        </small>
    `;

        applicationLogContainer.appendChild(
            row
        );

        applicationLogContainer.scrollTop = (
            applicationLogContainer.scrollHeight
        );
    }

    // =========================
    // Ejecutar aplicación real
    // =========================
    async function simulateApplicationProcess(formData ) {
        try {
            updateApplicationProgress(
                10,
                "Iniciando aplicación",
                "Enviando configuración..."
            );

            appendApplicationLog(
                "[10%] Enviando datos al servidor..."
            );

            const response = await fetch(
                `/aplicar-prehecho/${plantillaId}/apply/`,
                {
                    method: "POST",
                    body: formData,
                    headers: {
                        "X-CSRFToken": getCSRFToken()
                    }
                }
            );

            updateApplicationProgress(
                70,
                "Procesando plantilla",
                "Aplicando configuración..."
            );

            appendApplicationLog(
                "[70%] Procesando aplicación..."
            );

            const data = await response.json();

            // =========================
            // Error backend
            // =========================
            if (!data.success) {

                updateApplicationProgress(
                    100,
                    "Error en aplicación",
                    "La plantilla no pudo aplicarse."
                );

                appendApplicationLog(
                    `[ERROR] ${data.message}`
                );

                applicationProgressBar.classList.remove(
                    "progress-bar-animated"
                );

                applicationProgressBar.classList.add(
                    "bg-danger"
                );

                btnContinuar.disabled = false;

                btnContinuar.innerText = (
                    "Reintentar"
                );

                currentStep = "metadata";

                setActiveStep(
                    "metadata"
                );

                setContentTitle(
                    "Pre-configuración de plantilla"
                );

                return;
            }

            // =========================
            // Success
            // =========================
            updateApplicationProgress(
                100,
                "Plantilla aplicada",
                "Proceso completado correctamente."
            );

            appendApplicationLog(
                "[100%] Plantilla aplicada correctamente."
            );

            applicationProgressBar.classList.remove(
                "progress-bar-animated"
            );

            applicationProgressBar.classList.add(
                "bg-success"
            );

            btnContinuar.disabled = false;

            btnContinuar.innerText = (
                "Finalizar"
            );

            currentStep = "finish";

            setActiveStep("finish");

            setContentTitle("Proceso finalizado");

            showFinishState();

        } catch (error) {

            console.error(error);

            updateApplicationProgress(
                100,
                "Error inesperado",
                "Ocurrió un error durante la aplicación."
            );

            appendApplicationLog(
                `[ERROR] ${error}`
            );

            applicationProgressBar.classList.remove(
                "progress-bar-animated"
            );

            applicationProgressBar.classList.add(
                "bg-danger"
            );

            btnContinuar.disabled = false;

            btnContinuar.innerText = (
                "Reintentar"
            );
        }
    }

    // =========================
    // Delay helper
    // =========================
    function delay(ms) {
        return new Promise((resolve) => {
            setTimeout(resolve, ms);
        });
    }

    // =========================
    // Limpiar errores visuales
    // =========================
    function clearFieldErrors() {

        const invalids = document.querySelectorAll(
            ".is-invalid"
        );

        invalids.forEach((field) => {
            field.classList.remove(
                "is-invalid"
            );
        });

        const feedbacks = document.querySelectorAll(
            ".invalid-feedback.dynamic-error"
        );

        feedbacks.forEach((item) => {
            item.remove();
        });
    }

    // =========================
    // Mostrar error campo
    // =========================
    function showFieldError(
        field,
        message
    ) {

        field.classList.add(
            "is-invalid"
        );

        const feedback = document.createElement(
            "div"
        );

        feedback.className = (
            "invalid-feedback dynamic-error"
        );

        feedback.innerText = message;

        field.parentNode.appendChild(
            feedback
        );
    }

    // =========================
    // Validar metadata
    // =========================
    function validateMetadataForm() {

        let valid = true;

        metadataDefinition.forEach((item) => {

            const variable = (
                item.variable || ""
            );

            const tipo = (
                item.tipo || "texto"
            );

            const required = (
                item.required || false
            );

            const field = document.getElementById(
                variable
            );

            if (!field) {
                return;
            }

            // =========================
            // FILES
            // =========================
            if (
                tipo === "imagen" ||
                tipo === "p12"
            ) {

                if (
                    required &&
                    !field.files.length
                ) {

                    valid = false;

                    showFieldError(
                        field,
                        "Este archivo es obligatorio."
                    );
                }

                return;
            }

            const value = (
                field.value || ""
            ).trim();

            // =========================
            // Required
            // =========================
            if (
                required &&
                !value
            ) {

                valid = false;

                showFieldError(
                    field,
                    "Este campo es obligatorio."
                );

                return;
            }

            // =========================
            // Email
            // =========================
            if (
                tipo === "email" &&
                value
            ) {

                const emailRegex = (
                    /^[^\s@]+@[^\s@]+\.[^\s@]+$/
                );

                if (
                    !emailRegex.test(value)
                ) {

                    valid = false;

                    showFieldError(
                        field,
                        "Correo inválido."
                    );
                }
            }
        });

        return {
            valid
        };
    }

    // =========================
    // Recopilar metadata
    // =========================
    function collectMetadataFormData() {

        const formData = new FormData();

        metadataDefinition.forEach((item) => {

            const variable = (
                item.variable || ""
            );

            const tipo = (
                item.tipo || "texto"
            );

            const field = document.getElementById(
                variable
            );

            if (!field) {
                return;
            }

            // =========================
            // Files
            // =========================
            if (
                tipo === "imagen" ||
                tipo === "p12"
            ) {

                if (field.files.length) {

                    formData.append(
                        variable,
                        field.files[0]
                    );
                }

                return;
            }

            formData.append(
                variable,
                field.value
            );
        });

        return formData;
    }

    // =========================
    // Render metadata
    // =========================
    function renderMetadataForm() {

        // =========================
        // Sin metadata
        // =========================
        if (!metadataDefinition.length) {

            metadataContainer.innerHTML = `
                <div class="alert alert-info mb-0">
                    Esta plantilla no requiere
                    configuración adicional.
                </div>
            `;

            return;
        }

        let html = `
            <form id="formMetadataPlantilla">
        `;

        metadataDefinition.forEach((item) => {
            html += buildField(item);
        });

        html += `
            </form>
        `;

        metadataContainer.innerHTML = html;
    }

    // =========================
    // Construir campo
    // =========================
    function buildField(item) {

        const variable = item.variable || "";
        const label = item.label || variable;
        const tipo = item.tipo || "texto";
        const helpText = item.help_text || "";
        const validaciones = item.validaciones || {};

        let inputHtml = "";

        // =========================
        // Texto
        // =========================
        if (tipo === "texto") {

            inputHtml = `
                <input
                    type="text"
                    class="form-control"
                    id="${variable}"
                    name="${variable}"
                >
            `;
        }

        // =========================
        // Textarea
        // =========================
        else if (tipo === "textarea") {

            inputHtml = `
                <textarea
                    class="form-control"
                    id="${variable}"
                    name="${variable}"
                    rows="4"
                ></textarea>
            `;
        }

        // =========================
        // Email
        // =========================
        else if (tipo === "email") {

            inputHtml = `
                <input
                    type="email"
                    class="form-control"
                    id="${variable}"
                    name="${variable}"
                >
            `;
        }

        // =========================
        // Número / Decimal
        // =========================
        else if (
            tipo === "numero" ||
            tipo === "decimal"
        ) {

            inputHtml = `
                <input
                    type="number"
                    class="form-control"
                    id="${variable}"
                    name="${variable}"
                    step="${tipo === "decimal" ? "0.01" : "1"}"
                >
            `;
        }

        // =========================
        // Fecha
        // =========================
        else if (tipo === "fecha") {

            inputHtml = `
                <input
                    type="date"
                    class="form-control"
                    id="${variable}"
                    name="${variable}"
                >
            `;
        }

        // =========================
        // Imagen
        // =========================
        else if (tipo === "imagen") {

            const accept = (
                validaciones.extensiones || []
            ).join(",");

            inputHtml = `
                <input
                    type="file"
                    class="form-control"
                    id="${variable}"
                    name="${variable}"
                    accept="${accept}"
                >
            `;
        }

        // =========================
        // P12
        // =========================
        else if (tipo === "p12") {

            inputHtml = `
                <input
                    type="file"
                    class="form-control"
                    id="${variable}"
                    name="${variable}"
                    accept=".p12"
                >
            `;
        }

        // =========================
        // Select
        // =========================
        else if (tipo === "select") {

            const options = (
                validaciones.options || []
            );

            let optionsHtml = `
                <option value="">
                    Seleccione una opción
                </option>
            `;

            options.forEach((option) => {

                optionsHtml += `
                    <option value="${option.value}">
                        ${option.label}
                    </option>
                `;
            });

            inputHtml = `
                <select
                    class="form-control"
                    id="${variable}"
                    name="${variable}"
                >
                    ${optionsHtml}
                </select>
            `;
        }

        // =========================
        // Tipo no soportado
        // =========================
        else {

            inputHtml = `
                <div class="alert alert-warning mb-0">
                    Tipo no soportado: ${tipo}
                </div>
            `;
        }

        return `
            <div class="form-group mb-4">

                <label for="${variable}">
                    ${label}
                </label>

                ${inputHtml}

                ${helpText
                ?
                `
                    <small class="form-text text-muted">
                        ${helpText}
                    </small>
                    `
                :
                ""
            }

            </div>
        `;
    }

    function showFinishState() {
        applicationProgressBar.style.width = "100%";
        applicationProgressBar.innerText = "100%";

        applicationProgressBar.parentElement.classList.add("d-none");

        applicationProgressBar.classList.remove("progress-bar-animated");
        applicationProgressBar.classList.add("bg-success");

        applicationStatusTitle.innerText = "Aplicación completada";
        applicationStatusDescription.innerText =
            "La plantilla fue aplicada correctamente. Ya puedes volver al dashboard.";

        applicationLogContainer.innerHTML = `
            <div class="alert alert-success mb-0">
                Todo el proceso finalizó correctamente.
            </div>
        `;

        btnContinuar.innerText = "Ir al dashboard";
        btnContinuar.disabled = false;

        btnContinuar.onclick = () => {
            window.location.href = "/dashboard/";
        };
    }
});

