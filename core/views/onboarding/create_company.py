# core/views/onboarding/create_company.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction

from core.db.sqlite.models.user import User
from core.db.sqlite.models.company import Company
from core.db.sqlite.models.user_company import UserCompany
from core.db.sqlite.models.mongo_server import MongoServer
from core.db.sqlite.models.mysql_server import MySQLServer

from core.db.mongo.services.provision_service import MongoProvisionService
from core.db.mysql.services.provision_company_database import MySQLProvisionService

from core.services.company_logo_service import CompanyLogoService
from core.services.company_storage_service import CompanyStorageService
from core.services.company_validation_service import CompanyValidationService
from core.services.sri_ruc_service import SriRucService


def create_company_view(request):
    """
    Onboarding: creación de empresa

    Requisitos:
    - Usuario autenticado
    - Usuario SIN empresa activa
    """

    # =========================
    # Usuario autenticado
    # =========================
    user_id = request.session.get("user_id")

    if not user_id:
        request.session.flush()
        return redirect("accounts:login")

    try:
        user = User.objects.get(id=user_id, is_active=True)
    except User.DoesNotExist:
        request.session.flush()
        return redirect("accounts:login")

    # Si ya tiene empresa activa → dashboard
    if UserCompany.objects.filter(user=user, is_active=True).exists():
        return redirect("core:dashboard")

    # =========================
    # POST
    # =========================
    if request.method == "POST":

        # =========================
        # Datos generales
        # =========================
        erp_ruc = request.POST.get("erp_Ruc", "").strip()
        erp_razon_social = request.POST.get("erp_RazonSocial", "").strip()
        erp_nombre_comercial = request.POST.get("erp_NombreComercial", "").strip()
        erp_direccion = request.POST.get("erp_Direccion", "").strip()

        # =========================
        # Datos tributarios
        # =========================
        erp_es_contribuyente = request.POST.get(
            "erp_EsContribuyenteEspecial", "0"
        )

        erp_numero_contribuyente = "0"
        if erp_es_contribuyente == "1":
            erp_numero_contribuyente = request.POST.get(
                "erp_NumeroContribuyenteEspecial", "0"
            ).strip()

        erp_obligado = request.POST.get(
            "erp_ObligadoContabilidad", "NO"
        )

        erp_regimen = request.POST.get(
            "erp_Regimen", "No"
        )

        erp_agente_retencion = request.POST.get(
            "erp_AgenteRetencion", "No"
        )

        erp_confirmacion = request.POST.get("erp_Confirmacion")

        # =========================
        # Validaciones básicas
        # =========================
        if not erp_confirmacion:
            messages.error(
                request,
                "Debes confirmar la información para continuar"
            )
            return render(
                request,
                "core/onboarding/create_company.html",
                {"user": user}
            )

        if not all([
            erp_ruc,
            erp_razon_social,
            erp_nombre_comercial,
            erp_direccion,
        ]):
            messages.error(
                request,
                "Todos los campos obligatorios deben completarse"
            )
            return render(
                request,
                "core/onboarding/create_company.html",
                {"user": user}
            )

        # =========================
        # Validaciones de negocio
        # =========================
        try:
            CompanyValidationService.validate_ruc_not_exists(erp_ruc)
            SriRucService.validate_ruc(erp_ruc)
        except ValidationError as e:
            messages.error(request, e.message)
            return render(
                request,
                "core/onboarding/create_company.html",
                {"user": user}
            )

        # =========================
        # Servidores disponibles
        # =========================
        try:
            mongo_server = MongoServer.objects.get(
                is_default=True,
                status="DISPONIBLE"
            )
            mysql_server = MySQLServer.objects.get(
                is_default=True,
                status="DISPONIBLE"
            )
        except (MongoServer.DoesNotExist, MySQLServer.DoesNotExist):
            messages.error(
                request,
                "No hay servidores disponibles para crear la empresa"
            )
            return render(
                request,
                "core/onboarding/create_company.html",
                {"user": user}
            )

        # =========================
        # Transacción completa
        # =========================
        try:
            with transaction.atomic():

                # =========================
                # Crear empresa
                # =========================
                company = Company.objects.create(
                    ruc=erp_ruc,
                    razon_social=erp_razon_social,
                    nombre_comercial=erp_nombre_comercial,
                    direccion=erp_direccion,

                    contribuyente=erp_numero_contribuyente,
                    obligado=erp_obligado,
                    regimen=erp_regimen,
                    agente_retencion=erp_agente_retencion,

                    mongo_server=mongo_server,
                    mongo_db_name="",

                    mysql_server=mysql_server,
                    mysql_db_name="",
                    mysql_db_user="",
                    mysql_db_password="",

                    is_active=True
                )

                # =========================
                # Nombres de bases
                # =========================
                company.mongo_db_name = f"clt_mongo_{company.id}_auto"
                company.mysql_db_name = f"clt_mysql_{company.id}_auto"

                # =========================
                # Provisioning
                # =========================
                MongoProvisionService.provision_company_database(
                    mongo_uri=mongo_server.uri,
                    db_name=company.mongo_db_name,
                )

                mysql_credentials = (
                    MySQLProvisionService.provision_company_database(
                        mysql_server=mysql_server,
                        db_name=company.mysql_db_name,
                    )
                )

                company.mysql_db_user = mysql_credentials["db_user"]
                company.mysql_db_password = mysql_credentials["db_password"]
                company.save()

                # =========================
                # Storage
                # =========================
                CompanyStorageService.create_company_directories(
                    company_uid=str(company.id)
                )
                # Logo opcional
                erp_logo_file = request.FILES.get("erp_LogoFile")
                if erp_logo_file:
                    # CompanyLogoService.save_logo(
                    url_path = CompanyLogoService.save_logo(
                        company_uid=str(company.id),
                        logo_file=erp_logo_file
                    )
                    company.logo_url = url_path
                    company.save()
                    
                # =========================
                # Relación usuario - empresa
                # =========================
                UserCompany.objects.create(
                    user=user,
                    company=company,
                    is_owner=True,
                    is_active=True,
                    role_slug="owner"
                )

                request.session["company_id"] = company.id

        except ValidationError as e:
            messages.error(request, str(e))
            return render(
                request,
                "core/onboarding/create_company.html",
                {"user": user}
            )

        except Exception:
            messages.error(
                request,
                "Ocurrió un error al crear la empresa. Inténtalo nuevamente."
            )
            return render(
                request,
                "core/onboarding/create_company.html",
                {"user": user}
            )

        messages.success(request, "Empresa creada correctamente")
        return redirect("core:dashboard")

    # =========================
    # GET
    # =========================
    return render(
        request,
        "core/onboarding/create_company.html",
        {
            "user": user,
        }
    )
