document.addEventListener('DOMContentLoaded', function () {

    const form = document.querySelector('form');

    const selectContribuyente = document.getElementById('erp_EsContribuyenteEspecial');
    const inputNumeroContribuyente = document.getElementById('erp_NumeroContribuyenteEspecial');
    const checkboxConfirmacion = document.getElementById('confirmacion');
    const jsMessages = document.getElementById('create-company-messages');

    const submitButton = document.getElementById('btn-submit');
    const btnText = submitButton.querySelector('.btn-text');
    const btnSpinner = submitButton.querySelector('.btn-spinner');


    // =========================
    // Helpers
    // =========================
    function showErrors(errors) {
        jsMessages.innerHTML = '';
        jsMessages.style.display = 'block';

        errors.forEach(msg => {
            const div = document.createElement('div');
            div.className = 'alert alert-danger';
            div.textContent = msg;
            jsMessages.appendChild(div);
        });

        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function clearErrors() {
        jsMessages.innerHTML = '';
        jsMessages.style.display = 'none';
    }

    function setSubmitting(isSubmitting) {
        if (isSubmitting) {
            submitButton.disabled = true;
            btnText.classList.add('d-none');
            btnSpinner.classList.remove('d-none');
        } else {
            submitButton.disabled = false;
            btnText.classList.remove('d-none');
            btnSpinner.classList.add('d-none');
        }
    }


    // =========================
    // Toggle contribuyente especial
    // =========================
    function toggleContribuyenteEspecial() {
        if (selectContribuyente.value === '1') {
            inputNumeroContribuyente.disabled = false;
            inputNumeroContribuyente.required = true;
        } else {
            inputNumeroContribuyente.disabled = true;
            inputNumeroContribuyente.required = false;
            inputNumeroContribuyente.value = '';
        }
    }

    selectContribuyente.addEventListener('change', toggleContribuyenteEspecial);

    // Ejecutar al cargar por si hay valores previos
    toggleContribuyenteEspecial();

    // =========================
    // Validación antes del submit
    // =========================
    form.addEventListener('submit', function (e) {
        clearErrors();

        const errors = [];

        // Campos obligatorios (manual, explícito)
        const requiredFields = [
            { name: 'erp_Ruc', label: 'RUC' },
            { name: 'erp_RazonSocial', label: 'Razón social' },
            { name: 'erp_NombreComercial', label: 'Nombre comercial' },
            { name: 'erp_Direccion', label: 'Dirección' }
        ];

        requiredFields.forEach(field => {
            const input = form.querySelector(`[name="${field.name}"]`);
            if (!input || input.value.trim() === '') {
                errors.push(`El campo "${field.label}" es obligatorio.`);
            }
        });

        // Validación contribuyente especial
        if (selectContribuyente.value === '1') {
            if (inputNumeroContribuyente.value.trim() === '') {
                errors.push(
                    'Debes ingresar el número de Contribuyente Especial.'
                );
            }
        }

        // Confirmación
        if (!checkboxConfirmacion.checked) {
            errors.push(
                'Debes confirmar que la información es correcta para continuar.'
            );
        }

        // Si hay errores, no enviar POST
        if (errors.length > 0) {
            e.preventDefault();
            setSubmitting(false);
            showErrors(errors);
            return;
        }

        // Si no hay errores JS → bloquear botón y dejar que el POST continúe
        setSubmitting(true);


    });

    // Asegurar estado inicial
    setSubmitting(false);


});
