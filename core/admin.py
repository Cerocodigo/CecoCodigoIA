# core/admin.py

from django.contrib import admin

from core.db.sqlite.models.user import User
from core.db.sqlite.models.company import Company
from core.db.sqlite.models.user_company import UserCompany
from core.db.sqlite.models.company_invitation import CompanyInvitation
from core.db.sqlite.models.company_join_request import CompanyJoinRequest
from core.db.sqlite.models.mongo_server import MongoServer
from core.db.sqlite.models.mysql_server import MySQLServer
from core.db.sqlite.models.password_reset_token import PasswordResetToken


# =========================
# User
# =========================
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "first_name",
        "last_name",
        "is_active",
        "created_at",
    )
    search_fields = ("email", "first_name", "last_name")
    list_filter = ("is_active",)
    ordering = ("-created_at",)


# =========================
# Company
# =========================
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = (
        "razon_social",
        "ruc",
        "nombre_comercial",
        "is_active",
        "created_at",
    )
    search_fields = ("razon_social", "ruc", "nombre_comercial")
    list_filter = ("is_active",)
    ordering = ("-created_at",)


# =========================
# User ↔ Company
# =========================
@admin.register(UserCompany)
class UserCompanyAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "company",
        "is_owner",
        "is_active",
        "joined_at",
    )
    list_filter = ("is_owner", "is_active")
    search_fields = ("user__email", "company__razon_social")
    ordering = ("-joined_at",)


# =========================
# Company Invitation
# =========================
@admin.register(CompanyInvitation)
class CompanyInvitationAdmin(admin.ModelAdmin):
    list_display = (
        "company",
        "token",
        "is_general",
        "email",
        "requires_approval",
        "is_used",
        "expires_at",
        "created_at",
    )
    list_filter = (
        "is_general",
        "requires_approval",
        "is_used",
    )
    search_fields = (
        "token",
        "email",
        "company__razon_social",
    )
    ordering = ("-created_at",)
    readonly_fields = ("token", "created_at")


# =========================
# Company Join Request
# =========================
@admin.register(CompanyJoinRequest)
class CompanyJoinRequestAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "company",
        "is_approved",
        "created_at",
        "decided_at",
    )
    list_filter = ("is_approved",)
    search_fields = (
        "user__email",
        "company__razon_social",
    )
    ordering = ("-created_at",)


# =========================
# Mongo Servers
# =========================
@admin.register(MongoServer)
class MongoServerAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "status",
        "is_default",
        "created_at",
    )
    list_filter = ("status", "is_default")
    ordering = ("name",)


# =========================
# MySQL Servers
# =========================
@admin.register(MySQLServer)
class MySQLServerAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "host",
        "port",
        "status",
        "is_default",
        "created_at",
    )
    list_filter = ("status", "is_default")
    ordering = ("name",)

# =========================
# Password Reset Token
# =========================
@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "token",
        "used",
        "expires_at",
        "created_at",
    )
    list_filter = ("used",)
    search_fields = ("user__email", "token")
    ordering = ("-created_at",)