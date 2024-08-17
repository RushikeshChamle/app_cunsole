from django.urls import path

from app_cunsole.customer.views import bulk_create_customers,get_email_triggers, send_reminders, create_email_trigger
from app_cunsole.customer.views import create_customer
from app_cunsole.invoices.views import get_customer_invoice_summary
from app_cunsole.invoices.views import get_customers_by_account
from app_cunsole.invoices.views import get_user_account


urlpatterns = [
    path(
        "bulk_create_customers/",
        bulk_create_customers,
        name="bulk_create_customers",
    ),  # Endpoint for creating a new customer
    path("customers/", get_customers_by_account, name="get_customers_by_account"),
    path(
        "cutomerinvoices/",
        get_customer_invoice_summary,
        name="get_customer_invoice_summary",
    ),
    path("get_user_account/", get_user_account, name="get_user_account"),
    path("create_customer/",create_customer,name="create_customer"),  # Endpoint for creating a new customer
    path('send_reminders/',send_reminders, name='send_reminders'),
    path('create_email_trigger/', create_email_trigger, name='create_email_trigger'),
    path('get_email_triggers/', get_email_triggers, name='get_email_triggers'),
]


# localhost:8000/customers/create_customer
