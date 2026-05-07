
function agregarMensaje(texto, tipo="user") {
    const chatBox = document.getElementById("chatBox");

    const div = document.createElement("div");
    div.style.textAlign = tipo === "user" ? "right" : "left";
    div.style.marginBottom = "8px";

    div.innerHTML = `
        <span style="
            display:inline-block;
            padding:8px;
            border-radius:10px;
            background:${tipo === "user" ? "#007bff" : "#eee"};
            color:${tipo === "user" ? "#fff" : "#000"};
        ">${texto}</span>
    `;

    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
}

async function enviarMensaje() {
    const mensaje = document.getElementById("mensaje").value;
    const archivos = document.getElementById("archivo").files;

    agregarMensaje(mensaje, "user");

    document.getElementById("loadingIA").style.display = "flex";



    const formData = new FormData();
    formData.append("mensaje", mensaje);
    formData.append("previos", chatBox.innerText);

    

    for (let i = 0; i < archivos.length; i++) {
        formData.append("files", archivos[i]);
    }

    const response = await fetch(`/module/${window.moduleId}/edit/ia/chat-requerimientos/`, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCSRFToken()
        },
        body: formData
    });

    const data = await response.json();
    
    document.getElementById("loadingIA").style.display = "none";

    agregarMensaje(data.respuesta || "OK", "bot");

    if (data.modelo_cab) {
        window.modelo_cab = data.modelo_cab;
        // opcional: guardarlo en localStorage
        localStorage.setItem("modelo_cab", JSON.stringify(data.modelo_cab));
    }
    if (data.modelos_det) {
        window.modelos_det = data.modelos_det;
        // opcional: guardarlo en localStorage
        localStorage.setItem("modelos_det", JSON.stringify(data.modelos_det));
    }
    
        

    // 🔥 recargar formulario después de IA
    recargarFormulario()
}

function getCSRFToken() {
    return document.cookie.split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
}


function recargarFormulario() {
    const url = window.location.href;

    fetch(url, {
        headers: {
            "X-Requested-With": "XMLHttpRequest"
        }
    })
    .then(res => res.text())
    .then(html => {
        // Crear DOM temporal
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, "text/html");

        // Extraer SOLO el formulario nuevo
        const nuevo = doc.querySelector("#contenedor-formulario");

        if (nuevo) {
            document.querySelector("#contenedor-formulario").innerHTML = nuevo.innerHTML;
        } else {
            console.error("No se encontró el contenedor en la respuesta");
        }
    })
    .catch(err => console.error("Error recargando formulario:", err));
}