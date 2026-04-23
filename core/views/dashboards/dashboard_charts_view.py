# core/views/dashboards/dashboard_charts_view.py

from django.shortcuts import redirect
from django.http import JsonResponse, Http404
from core.db.sqlite.models.user import User

from django.views.decorators.http import require_GET

from core.services.dashboard.dashboard_chart_service import (
    DashboardChartService,
)


@require_GET
def dashboards_charts_view(request):
    # =========================
    # Usuario, empresa y relación usuario-empresa del contexto
    # =========================
    user = request.user_ctx
    company = request.company_ctx
    user_company = request.user_company_ctx

    if not user or not company or not user_company:
        raise Http404("Contexto inválido")
    

    try:
        context = DashboardChartService.cargar_charts(
            company=company
        )
    except Exception as e:
        import traceback
        traceback.print_exc()

        return JsonResponse(
            {"error": str(e)},
            status=500,
        )

    return JsonResponse(context, status=200, safe=True)
