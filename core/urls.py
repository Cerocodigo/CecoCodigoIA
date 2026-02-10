from django.urls import path

from core.views.onboarding.select_company import select_company_view
from core.views.onboarding.create_company import create_company_view
from core.views.onboarding.join_company import join_company

from core.views.dashboard import dashboard_view
from core.views.company_join_requests import (approve_join_request,reject_join_request)
from core.views.modules.create_module_view import (create_module_view)
from core.views.modules.module_main_view import (module_main_view)

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
    path("module/create/",create_module_view,name="create_module"),
    path("module/<slug:module_id>/main/", module_main_view, name="module_main")


    
]
