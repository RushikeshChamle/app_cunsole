from django.urls import path

from app_cunsole.invoices.views import bulk_create_invoices
from app_cunsole.invoices.views import create_invoice
from app_cunsole.invoices.views import get_invoices_by_account,credit_sales_card_data,invoice_payment_card,get_top_due_customers,dso_data_card,ar_status_card, invoice_summary_cards, check_email_trigger, get_customer_summary,invoice_details, add_payment, get_customer_payments
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
    path('get_customer_summary/<uuid:customer_id>/', get_customer_summary, name='get_customer_summary'),
    path('get_customer_payments/<uuid:customer_id>/', get_customer_payments, name='get_customer_payments'),
    path('invoice_details/<int:invoice_id>/', invoice_details, name='invoice_details'),
    path('check_email_trigger/<int:invoice_id>/', check_email_trigger, name='check_email_trigger'),
    path('add_payment/', add_payment, name='add_payment'),
    path('invoice_summary_cards/', invoice_summary_cards, name='invoice_summary_cards'),
    path('dso_data_card/', dso_data_card, name='dso-data'),
    path('ar_status_card/', ar_status_card, name='ar_status_card'),
    path('get_top_due_customers/', get_top_due_customers, name='get_top_due_customers'),
    path('invoice_payment_card/', invoice_payment_card, name='invoice_payment_card'),
    path('credit_sales_card_data/', credit_sales_card_data, name='credit_sales_card_data'),
    
]
