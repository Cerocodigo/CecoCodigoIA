document.addEventListener('DOMContentLoaded', function () {

    const form = document.querySelector('form');

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
    // Validación antes del submit
    // =========================
    form.addEventListener('submit', function (e) {
        clearErrors();

        const errors = [];

        const requiredFields = [
            { name: 'erp_NombreComercial', label: 'Nombre comercial' },
            { name: 'erp_Pais', label: 'País' }
        ];

        requiredFields.forEach(field => {
            const input = form.querySelector(`[name="${field.name}"]`);
            if (!input || !input.value || input.value.trim() === '') {
                errors.push(`El campo "${field.label}" es obligatorio.`);
            }
        });


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
