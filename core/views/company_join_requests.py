# core/views/company_join_requests.py

from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import ValidationError

from core.db.sqlite.services.company_join_request_service import (
    CompanyJoinRequestService
)


def approve_join_request(request, request_id: int):
    try:
        CompanyJoinRequestService.approve(request_id, request.user)
        messages.success(request, "Solicitud aprobada correctamente")
    except ValidationError as e:
        messages.error(request, str(e))

    return redirect("core:dashboard")


def reject_join_request(request, request_id: int):
    try:
        CompanyJoinRequestService.reject(request_id, request.user)
        messages.info(request, "Solicitud rechazada")
    except ValidationError as e:
        messages.error(request, str(e))

    return redirect("core:dashboard")
