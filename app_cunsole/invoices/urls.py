from django.urls import path

from app_cunsole.invoices.views import bulk_create_invoices
from app_cunsole.invoices.views import create_invoice
from app_cunsole.invoices.views import get_invoices_by_account
from app_cunsole.users.views import CustomTokenObtainPairView
from .views import send_email_view
# from app_cunsole.users.views import TokenRefreshView
from app_cunsole.users.views import signup


urlpatterns = [
    path(
        "createinvoice/",
        create_invoice,
        name="create_invoice",
    ),  # Endpoint for creating a new invoice
    path("signup/", signup, name="signup"),
    path("signin/", CustomTokenObtainPairView.as_view(), name="signin"),
    # path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path(
        "create_invoice/",
        create_invoice,
        name="create_invoice",
    ),  # Endpoint for creating a new invoice
    path(
        "bulk_invoices/",
        bulk_create_invoices,
        name="bulk_invoices",
    ),  # Endpoint for creating a new invoice
    path(
        "get_invoices_by_account/",
        get_invoices_by_account,
        name="get_invoices_by_account",
    ),
    path('send_email_view/', send_email_view, name='send_email_view'),
]
