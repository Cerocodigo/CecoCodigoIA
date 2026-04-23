function getCSRFToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : null;
}

function handleLogoError(img) {
    img.dataset.logoLoaded = "false";
    img.style.display = "none";

    const icon = document.createElement("i");
    icon.className = "fas fa-user-circle fa-lg";

    img.parentNode.appendChild(icon);
}

document.addEventListener("DOMContentLoaded", function () {
    const img = document.getElementById("company-logo");

    if (!img) return;

    // Si ya está cargada (cache)
    if (img.complete) {
        if (img.naturalWidth > 0) {
            img.dataset.logoLoaded = "true";
        } else {
            handleLogoError(img);
        }
        return;
    }

    // Cuando carga correctamente
    img.addEventListener("load", function () {
        img.dataset.logoLoaded = "true";
    });

    // Cuando falla
    img.addEventListener("error", function () {
        handleLogoError(img);
    });
});