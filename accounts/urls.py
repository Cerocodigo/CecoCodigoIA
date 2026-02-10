from django.urls import path
from accounts.views.login import login_view
from accounts.views.logout import logout_view
from accounts.views.register_user import register_user_view
from accounts.views.activate_account import activate_account_view
from accounts.views.password_reset_request import password_reset_request_view
from accounts.views.password_reset_confirm import password_reset_confirm_view

app_name = "accounts"

urlpatterns = [
    path("", login_view, name="login"),
    path("logout/", logout_view, name="logout"),

    # Registro y activación
    path("register/user/", register_user_view, name="register_user"),
    path("register/activate/<str:activation_code>/", activate_account_view, name="activate_account"),

    # Recuperación de contraseña
    path("password-reset/confirm/<str:token>/",password_reset_confirm_view,name="password_reset_confirm"),
    path("password-reset/",password_reset_request_view,name="password_reset_request"),
]
