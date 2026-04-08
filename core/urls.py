from django.urls import path

from core.views.onboarding.select_company import select_company_view
from core.views.onboarding.create_company import create_company_view
from core.views.onboarding.join_company import join_company

from core.views.dashboard import dashboard_view
from core.views.company_join_requests import (approve_join_request,reject_join_request)
from core.views.modules.create_module_view import (create_module_view)
from core.views.modules.module_main_view import (module_main_view)
from core.views.modules.module_view_reg_view import (module_view_reg_view, module_delete_reg_view)

from core.views.modules.module_new_reg_view import (module_new_reg_view, calculosReferenciaBuscador, calculosNumeroSecuencial, calculosQueryBaseDatos)

from core.views.modules.sync_module_schema_view import (sync_module_schema_view,)

from core.views.reports.reports_main_view import reports_main_view

from core.views.reports.create_report_view import create_report_view
from core.views.reports.execute_report_view import execute_report_view

app_name = "core"

urlpatterns = [
    # Gestión de empresa
    path("select-company/", select_company_view, name="select_company"),
    path("create-company/", create_company_view, name="create_company"),
    path("join/<str:token>/", join_company, name="join_company"),

    # Dashboard y gestión de módulos
    path("dashboard/", dashboard_view, name="dashboard"),
    path("company/join-request/<int:request_id>/approve/",approve_join_request,name="approve_join_request"),
    path("company/join-request/<int:request_id>/reject/",reject_join_request,name="reject_join_request"),

    # Módulo
    path("module/create/",create_module_view,name="create_module"),
    path("module/<slug:module_id>/main/", module_main_view, name="module_main"),
    path("module/<slug:module_id>/new/", module_new_reg_view, name="module_new_reg"),
    path("calculosNumeroSecuencial/<str:modelo>/<str:campo>/",calculosNumeroSecuencial, name="calculosNumeroSecuencial"), ##calculosCampos 
    path("calculosQueryBaseDatos/<str:modelo>/<str:campo>/",calculosQueryBaseDatos, name="calculosQueryBaseDatos"),
    path("calculosReferenciaBuscador/<str:modelo>/<str:campo>/",calculosReferenciaBuscador, name="calculosReferenciaBuscador"),
    path("module/<slug:module_id>/view/<int:id>/", module_view_reg_view, name="module_view_reg_view"),
    path("module/<slug:module_id>/edit/<int:id>/", module_view_reg_view, name="module_edit_reg_view"),
    path("module/<slug:module_id>/delete/<int:id>/", module_delete_reg_view, name="module_delete_reg_view"),

    
    # # Endpoint de desarrollo para sincronizar esquema MySQL
    path("module/<slug:module_id>/validate-module/",sync_module_schema_view,name="validate_module",),


    # Reportes Dinámicos
    
    path("reports/<str:report_id>/main/",reports_main_view,name="report_main"),
    path("reports/api/execute/<str:report_id>/", execute_report_view, name="api_execute_report"),

    # path("reports/create/", reports_main_view, name="create_reports"),
    path("reports/api/create/", create_report_view, name="api_create_report"),
    
]
