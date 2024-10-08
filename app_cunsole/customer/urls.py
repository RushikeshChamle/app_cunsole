from django.urls import path

from app_cunsole.customer.views import bulk_create_customers,update_email_trigger,get_entire_account_invoice_reminders,get_all_invoice_reminders,get_invoice_with_all_reminders,get_account_invoice_reminders, get_next_invoice_reminder,get_customer,get_customers_by_account,get_email_triggers, get_email_trigger_by_id, send_reminders_emails,create_email_trigger, test_email_trigger
from app_cunsole.customer.views import create_customer
from app_cunsole.invoices.views import get_customer_invoice_summary
# from app_cunsole.invoices.views import get_customers_by_account
from app_cunsole.invoices.views import get_user_account



urlpatterns = [
    path(
        "bulk_create_customers/",
        bulk_create_customers,
        name="bulk_create_customers",
    ),  # Endpoint for creating a new customer
    path("customers/", get_customers_by_account, name="get_customers_by_account"),
    
    path(
        "customerinvoices/",
        get_customer_invoice_summary,
        name="customerinvoices",
    ),
    path("get_user_account/", get_user_account, name="get_user_account"),
    path("create_customer/",create_customer,name="create_customer"),  # Endpoint for creating a new customer
    path('send_reminders_emails/',send_reminders_emails, name='send_reminders_emails'),
    path('create_email_trigger/', create_email_trigger, name='create_email_trigger'),

    path('update_email_trigger/<uuid:trigger_id>/', update_email_trigger, name='update_email_trigger'),

   
    # Endpoint to retrieve all email triggers associated with the user account creation
    path('get_email_triggers/', get_email_triggers, name='get_email_triggers'),

    # Endpoint to manually test sending an email using a specified email trigger
    path('test_email_trigger/', test_email_trigger, name='test_email_trigger'),

    # Endpoint to retrieve a specific email trigger by its unique identifier
    path('email_trigger/<uuid:trigger_id>/', get_email_trigger_by_id, name='get_email_trigger_by_id'),

    # Endpoint to retrieve customer details using the customer's unique identifier
    path('get_customer/<uuid:customer_id>/', get_customer, name='get_customer'),

    # Endpoint to retrieve the next reminder for a specific invoice by its ID without dynamic fields
    path('invoices/<int:invoice_id>/next-reminder/', get_next_invoice_reminder, name='next_invoice_reminder'),

    # Endpoint to retrieve all upcoming reminders for a specific invoice by its ID with dynamic fields
    path('invoices/<int:invoice_id>/dynamic_next_reminders/', get_invoice_with_all_reminders, name='get_invoice_with_all_reminders'),

    # Endpoint to retrieve all reminders (both past and future) for a specific invoice by its ID
    path('invoices/<int:invoice_id>/all-reminders/', get_all_invoice_reminders, name='get_all_invoice_reminders'),

    # Endpoint to retrieve invoice reminders for the user's associated account
    path('account/invoice-reminders/', get_account_invoice_reminders, name='get_account_invoice_reminders'),

    # Endpoint to retrieve all invoice reminders (including past) for the user's associated account
    path('account/invoice-reminders-all/', get_entire_account_invoice_reminders, name='get_entire_account_invoice_reminders'),


]


