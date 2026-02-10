/**
 * Crea un nuevo módulo desde el sidebar
 * Llama al endpoint Django:
 * POST /core/module/create/
 */
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
