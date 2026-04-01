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
    # Usuario autenticado
    # =========================
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("accounts:login")

    try:
        user = User.objects.get(id=user_id, is_active=True)
    except User.DoesNotExist:
        request.session.flush()
        return redirect("accounts:login")

    company = getattr(request, "company_ctx", None)
    if not company:
        raise Http404("Empresa no disponible en el contexto")

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
