import json
from venv import logger
import jwt
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from django.conf import settings
# from config.settings.base import settings
from decimal import Decimal , InvalidOperation
from rest_framework.permissions import IsAuthenticated
from app_cunsole.customer.models import Customers
from app_cunsole.users.models import User
from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from .serializers import CustomerSerializer
import uuid
from django.core.mail import EmailMessage
from datetime import timedelta
from app_cunsole.invoices.models import Invoices
from django.shortcuts import render, get_object_or_404
from django.core.mail import send_mail
from django.utils import timezone
from django.http import JsonResponse


from .models import Account

from django.db import transaction

from .models import  EmailTrigger, Customers
from django.views import View

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import EmailTrigger


from .serializers import EmailTriggerSerializer
from django.views.decorators.csrf import csrf_exempt

import pandas as pd



@api_view(["POST"])
def create_customer(request):
    """
    Create a new customer record.

    This view requires that the user is authenticated. It uses the data from the request to create a new
    customer record linked to the authenticated user's account. The data is validated and serialized before
    saving the new customer record.

    Returns:
        Response: A JSON response indicating the result of the creation attempt.
                  If authentication is not provided, returns a 401 Unauthorized error.
                  If the data is invalid, returns a 400 Bad Request error.
    """
    try:
        if request.user_is_authenticated:
            user = request.user_id
            account = request.user_account

            if not account:
                return Response(
                    {"error": "User does not have an associated account"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Deserialize the request data
            data = request.data.copy()
            data['user'] = user
            data['account'] = account.id

            # Initialize serializer
            serializer = CustomerSerializer(data=data)

            # Validate and save
            if serializer.is_valid():
                customer = serializer.save()
                return Response(
                    {
                        "success": "Customer created successfully",
                        "customer": serializer.data,
                    },
                    status=status.HTTP_201_CREATED,
                )

            # Log validation errors
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"error": "Authentication required"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





@api_view(['GET'])
def get_active_customers_by_account(request):
    try:
        # Ensure the user is authenticated
        if request.user_is_authenticated:
            account = request.user_account

            if not account:
                return Response(
                    {"error": "User does not have an associated account"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            


            

            # Fetch active customers based on the account and isactive = True
            customers_list = Customers.objects.filter(account_id=account.id, isactive=True)

            # Check if any customers exist for the account
            if not customers_list.exists():
                return Response(
                    {"error": "No active customers found for the account"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Serialize the customer data
            serializer = CustomerSerializer(customers_list, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Return an error if the user is not authenticated
        return Response(
            {"error": "Authentication required"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    # Catch any unexpected exceptions and return a 500 error
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET'])
def get_customer(request, customer_id):
    """
    Retrieve a customer by their ID.

    This view retrieves a customer record by the provided customer ID. The customer must be associated
    with the authenticated user's account.

    Args:
        request (Request): The HTTP request object.
        customer_id (uuid.UUID): The UUID of the customer to retrieve.

    Returns:
        Response: A JSON response containing the customer data.
                  If the customer is not found, returns a 404 Not Found error.
                  If the user is not authenticated, returns a 401 Unauthorized error.
    """
    try:
        if request.user_is_authenticated:
            user = request.user_id
            account = request.user_account
            customer = Customers.objects.filter(account=account, id=customer_id).first()

            if customer:
                serializer = CustomerSerializer(customer)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"error": "Customer not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            return Response(
                {"error": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED
            )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )




# bulk create customers api previsus


@csrf_exempt
def bulk_create_customers(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed."}, status=405)

    try:
        if request.user_is_authenticated:
            user_id = request.user_id
            account_id = request.user_account.id

            if "file" not in request.FILES:
                return JsonResponse({"error": "No file uploaded"}, status=400)

            file = request.FILES["file"]
            
            if not file.name.endswith((".csv", ".xlsx")):
                return JsonResponse(
                    {"error": "Unsupported file type. Please upload a CSV or Excel file."},
                    status=400,
                )

            try:
                data = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
            except Exception as e:
                return JsonResponse({"error": f"Error reading file: {str(e)}"}, status=400)

            required_fields = ["name", "email"]
            missing_fields = [field for field in required_fields if field not in data.columns]
            if missing_fields:
                return JsonResponse({"error": f"Missing required fields: {', '.join(missing_fields)}"}, status=400)

            customers_to_create = []
            errors = []

            # Fetch the Account instance
            try:
                account = Account.objects.get(id=account_id)
            except Account.DoesNotExist:
                return JsonResponse({"error": "Invalid account"}, status=400)

            for index, row in data.iterrows():
                try:
                    customer = Customers(
                        externalid=row.get("externalid"),
                        name=row["name"],
                        email=row["email"],
                        phone=row.get("phone"),
                        address=row.get("address"),
                        city=row.get("city"),
                        state=row.get("state"),
                        country=row.get("country"),
                        postalcode=row.get("postalcode"),
                        taxid=row.get("taxid"),
                        companyname=row.get("companyname"),
                        industrytype=row.get("industrytype"),
                        paymentterms=row.get("paymentterms"),
                        creditlimit=Decimal(row.get("creditlimit", 0)),
                        notes=row.get("notes"),
                        isactive=row.get("isactive", True),
                        account=account,  # Use the Account instance
                        user_id=user_id,  # Use the user ID directly
                        website=row.get("website"),
                        currency=row.get("currency", "USD"),
                        discount=Decimal(row.get("discount", 0)),
                        account_balance=Decimal(row.get("account_balance", 0)),
                        customer_category=row.get("customer_category"),
                        risk_level=row.get("risk_level"),
                        erp_system=row.get("erp_system"),
                        crm_id=row.get("crm_id"),
                        referral_source=row.get("referral_source"),
                    )
                    customers_to_create.append(customer)
                except (ValueError, InvalidOperation) as e:
                    errors.append(f"Error in row {index + 2}: {str(e)}")

            if errors:
                return JsonResponse({"error": "Validation errors", "details": errors}, status=400)

            try:
                with transaction.atomic():
                    Customers.objects.bulk_create(customers_to_create, batch_size=100)
            except Exception as e:
                return JsonResponse({"error": f"Error creating customers: {str(e)}"}, status=500)

            return JsonResponse({"success": f"{len(customers_to_create)} customers created successfully"})
        else:
            return JsonResponse(
                {"error": "Authentication required"},
                status=401
            )
    except Exception as e:
        return JsonResponse(
            {"error": str(e)},
            status=500
        )


@api_view(["POST"])
def create_email_trigger(request):
    try:
        if request.user_is_authenticated:
            user = request.user_id
            account = request.user_account

            if not account:
                return Response(
                    {"error": "User does not have an associated account"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Prepare data for serializer
            data = request.data.copy()
            data['user'] = user
            data['account'] = account.id

            print("User ID API:", user)
            print("Account ID API:", account.id)
            print("Updated Data API:", data)

            # Initialize serializer
            serializer = EmailTriggerSerializer(data=data)

            print("Serialise API :", serializer)

            # Validate and save
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            # Log validation errors
            print("Serializer Errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"error": "Authentication required"},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




@api_view(["PUT"])
def update_email_trigger(request, trigger_id):
    try:
        if request.user_is_authenticated:
            user = request.user_id  # Check if this is an int or an object
            account = request.user_account  # Check if this is an int or an object

            # Ensure the account exists
            if not account:
                return Response(
                    {"error": "User does not have an associated account"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get the existing email trigger
            try:
                email_trigger = EmailTrigger.objects.get(id=trigger_id, account=account)
            except EmailTrigger.DoesNotExist:
                return Response(
                    {"error": "Email trigger not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Prepare data for serializer
            data = request.data.copy()

            # Assign user and account correctly based on their type (int or object)
            if isinstance(user, int):
                data['user'] = user  # If user is already an ID
            else:
                data['user'] = user.id  # If user is an object

            if isinstance(account, int):
                data['account'] = account  # If account is already an ID
            else:
                data['account'] = account.id  # If account is an object

            print("User ID API:", data['user'])
            print("Account ID API:", data['account'])
            print("Updated Data API:", data)

            # Initialize serializer with existing instance and new data
            serializer = EmailTriggerSerializer(email_trigger, data=data, partial=True)

            print("Serializer API:", serializer)

            # Validate and save
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)

            # Log validation errors
            print("Serializer Errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"error": "Authentication required"},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




@api_view(["GET"])
def get_email_triggers(request):
    """
    Retrieve all active email triggers for the authenticated user and their associated account.
    """
    if request.method == "GET":
        if not request.user_is_authenticated:
            return Response(
                {"error": "Authentication credentials were not provided."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Fetch the user's account from the middleware (already set)
        account = request.user_account
        user = request.user
        # print("data of account" + account)
        # print("Account ID:", account.id)  # Assuming account is a model instance with an 'id' field
        # print("Account ID:", user.id)  # Assuming account is a model instance with an 'id' field


        if not account:
            return Response(
                {"error": "User does not have an associated account"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Fetch active email triggers for the user's account
        email_triggers = EmailTrigger.objects.filter(account=account, isactive=True)

        if not email_triggers.exists():
            return Response(
                {"error": "No active email triggers found for the account"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Serialize the data
        serializer = EmailTriggerSerializer(email_triggers, many=True)

        # Return the response
        return Response({"email_triggers": serializer.data}, status=status.HTTP_200_OK)

    return Response({"error": "Method not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)



# @csrf_exempt
@api_view(["GET"])
def get_email_trigger_by_id(request, trigger_id):
    """
    Retrieve a specific email trigger by its ID.

    This view requires that the user is authenticated. It fetches the email trigger with the specified
    ID that is linked to the authenticated user's account and is marked as active. The data is serialized
    and returned in the response.

    Args:
        trigger_id (uuid): The ID of the email trigger to retrieve.

    Returns:
        Response: A JSON response containing the email trigger data and a status code.
                  If authentication is not provided, returns a 401 Unauthorized error.
                  If the email trigger is not found, returns a 404 Not Found error.
    """
    if request.user_is_authenticated:
        try:
            # Retrieve the authenticated user
            user = request.user_id

            # Retrieve the account associated with the authenticated user
            account = request.user_account

            # Retrieve the email trigger based on the ID and check if it belongs to the user and account
            email_trigger = EmailTrigger.objects.get(id=trigger_id, user=user, account=account, isactive=True)

            # Serialize the email trigger
            serializer = EmailTriggerSerializer(email_trigger)

            # Return the serialized data with a 200 OK status
            return Response(serializer.data, status=status.HTTP_200_OK)
        except EmailTrigger.DoesNotExist:
            # If the email trigger does not exist, return a 404 Not Found error
            return Response(
                {"error": "Email trigger not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
    else:
        # If the user is not authenticated, return a 401 Unauthorized error
        return Response(
            {"error": "Authentication credentials were not provided."},
            status=status.HTTP_401_UNAUTHORIZED,
        )


@api_view(["GET"])
def get_customers_by_account(request):
    try:
        # Ensure the user is authenticated (Updated)

        if request.user_is_authenticated:
            user = request.user_id
            account = request.user_account

            if not account:
                return Response(
                    {"error": "User does not have an associated account"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Fetch customers for the user's account using ORM queries
            account_customers = Customers.objects.filter(account_id=account.id)

            # Serialize the data
            serializer = CustomerSerializer(account_customers, many=True)

            # Return the response
            return Response({"customers": serializer.data}, status=status.HTTP_200_OK)

        return Response(
            {"error": "Authentication required"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





# new logic for getting account id
@shared_task
def send_reminders_emails_task():
    """
    Task to send reminder emails based on configured email triggers.
    This checks due dates and sends emails asynchronously.
    """
    today = timezone.now().date()
    triggers = EmailTrigger.objects.filter(isactive=True)
    sent_emails_info = []

    for trigger in triggers:
        # Calculate the target date based on trigger's condition
        if trigger.condition_type == 0:  # Before Due Date
            target_date = today + timezone.timedelta(days=trigger.days_offset)
        elif trigger.condition_type == 1:  # On Due Date
            target_date = today
        elif trigger.condition_type == 2:  # After Due Date
            target_date = today - timezone.timedelta(days=trigger.days_offset)
        else:
            continue

        # Get invoices matching the trigger's criteria
        invoices = Invoices.objects.filter(
            duedate=target_date,
            status__in=[0, 1],  # Due or Partial
            account=trigger.account
        )

        # Process each invoice and send emails
        for invoice in invoices:
            customer = Customers.objects.filter(id=invoice.customerid).first()
            if customer and customer.email:
                subject = trigger.email_subject
                body = trigger.email_body.format(
                    name=customer.name,
                    invoice_id=invoice.customid,
                    amount_due=invoice.total_amount - invoice.paid_amount,
                    status='Due' if invoice.status == 0 else 'Partial'
                )

                # Send the email asynchronously with account ID
                send_email_task.delay(
                    account_id=trigger.account.id,  # Pass account_id
                    to_email=customer.email,
                    subject=subject,
                    body=body
                )

                sent_emails_info.append({
                    "customer_email": customer.email,
                    "customer_name": customer.name,
                    "invoice_id": invoice.customid,
                    "amount_due": invoice.total_amount - invoice.paid_amount,
                })

    return sent_emails_info






from django.apps import apps
from celery import shared_task
from django.core.mail import send_mail

from django.contrib.auth import get_user_model
User = get_user_model()

# correct previous logic
# @shared_task
# def send_email_task(account_id, to_email, subject, body):
#     try:
#         # Default sender email
#         sender_email = 'info@cunsole.com'
#         print("Starting email sending process...")

#         # Get the necessary models from the Users app
#         User = apps.get_model('users', 'User')
#         Domainconfig = apps.get_model('users', 'Domainconfig')

#         # Fetch the account's default verified domain configuration
#         user = User.objects.filter(account_id=account_id).first()
#         domain_config = Domainconfig.objects.filter(
#             account=user.account, 
#             is_default=True, 
#             verification_status=True
#         ).first()

#         if domain_config:
#             print(f"Domain config found: {domain_config}")
#             if domain_config.mailing_address:
#                 sender_email = domain_config.mailing_address
#                 print(f"Using sender email: {sender_email}")
#             else:
#                 print("No mailing address found in domain config.")
#         else:
#             print("No active domain config found for this account.")

#         print(f"Preparing to send email:\nSubject: {subject}\nBody: {body}")

#         send_mail(
#             subject=subject,
#             message=body,
#             from_email=sender_email,
#             recipient_list=[to_email],
#             fail_silently=False,
#         )

#         print(f"Email sent successfully to {to_email} from {sender_email}")

#     except Exception as e:
#         print(f"Failed to send email to {to_email}: {str(e)}")
#         raise


from django.apps import apps
from celery import shared_task
from django.core.mail import send_mail
import logging

from django.contrib.auth import get_user_model
User = get_user_model()

# Configure logger
logger = logging.getLogger(__name__)

@shared_task
def send_email_task(account_id, to_email, subject, body):
    try:
        # Default sender email
        sender_email = 'info@cunsole.com'
        print("Starting email sending process...")

        # Get the necessary models from the Users app
        User = apps.get_model('users', 'User')
        Domainconfig = apps.get_model('users', 'Domainconfig')

        # Fetch the account's default verified domain configuration
        user = User.objects.filter(account_id=account_id).first()
        domain_config = Domainconfig.objects.filter(
            account=user.account, 
            is_default=True, 
            verification_status=True
        ).first()

        if domain_config:
            print(f"Domain config found: {domain_config}")
            if domain_config.mailing_address:
                sender_email = domain_config.mailing_address
                print(f"Using sender email: {sender_email}")
            else:
                print("No mailing address found in domain config.")
        else:
            print("No active domain config found for this account.")

        print(f"Preparing to send email:\nSubject: {subject}\nBody: {body}")

        send_mail(
            subject=subject,
            message=body,
            from_email=sender_email,
            recipient_list=[to_email],
            fail_silently=False,
        )

        print(f"Email sent successfully to {to_email} from {sender_email}")

    except Exception as e:
        # Log the error and re-raise the exception
        print(f"Failed to send email: {str(e)}")
        logger.error(f"Email sending failed: {str(e)}")
        raise



# @csrf_exempt
def send_reminders_emails(request):
    if request.method == 'POST':
        # Call the Celery task asynchronously
        result = send_reminders_emails_task.delay()

        return JsonResponse({
            "status": "Reminders are being sent asynchronously",
            "task_id": result.id  # Return the task ID for reference
        })
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)





# @csrf_exempt
@api_view(["POST"])
def test_email_trigger(request):
    """
    Handle POST requests to manually test an email trigger.

    - Retrieves a specified EmailTrigger record.
    - Sends a test email using the subject and body of the trigger.
    - Returns the email content and status in the response.
    """
    try:
        # Get the trigger ID from the request data
        trigger_id = request.data.get('trigger_id')

        # Retrieve the EmailTrigger record
        trigger = EmailTrigger.objects.filter(id=trigger_id, isactive=True).first()

        if not trigger:
            return Response({"error": "Email trigger not found or inactive"}, status=status.HTTP_404_NOT_FOUND)

        # Define a test customer email
        test_email = 'rushikeshchamle23@gmail.com'

        # Prepare the email subject and body using the trigger's data
        subject = trigger.email_subject.format(
            name='Cunsole',
            invoice_id='TEST123',
            amount_due='0.00',
            status='Due'  # You can change this to 'Partial' or other statuses for testing
        )

        body = trigger.email_body.format(
            name='Cunsole',
            invoice_id='INV001',
            amount_due='1000.00',
            status='Due'  # You can change this to 'Partial' or other statuses for testing
        )

        account_id = trigger.account_id 
        # Send the test email asynchronously
        send_email_task.delay(account_id, test_email, subject, body)

        return Response({
            "status": "Test email task initiated",
            "email_subject": subject,
            "email_body": body
        })

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    




@api_view(['GET'])
def get_next_invoice_reminder(request, invoice_id):
    """
    Retrieve the next reminders for a specified invoice.
    
    This API endpoint checks if there are any upcoming reminders for a given invoice
    based on active email triggers. It returns the reminder details if the invoice 
    is not fully paid. If the invoice is paid, it informs the user that no reminders 
    will be sent. 
    
    Parameters:
    - request: The HTTP request object.
    - invoice_id: The ID of the invoice to check for reminders.
    
    Returns:
    - A response containing reminder details or messages based on the invoice status.
    """


    try:
        # Fetch the invoice for the authenticated user's account
        invoice = Invoices.objects.get(id=invoice_id, account=request.user_account)

        # If the invoice is fully paid, no reminders are needed
        if invoice.status == 2:  # Assuming status 2 is 'Completed' or fully paid
            return Response({"message": "This invoice has been fully paid. No reminders will be sent."}, status=status.HTTP_200_OK)

        # Get all active email triggers for the user's account
        triggers = EmailTrigger.objects.filter(account=request.user_account, isactive=True)

        if not triggers:
            return Response({"message": "No active email triggers found for this account."}, status=status.HTTP_404_NOT_FOUND)

        today = timezone.now().date()
        reminders = []

        # Loop through each trigger and calculate the reminder dates
        for trigger in triggers:
            if trigger.condition_type == 0:  # Before Due Date
                reminder_date = invoice.duedate.date() - timedelta(days=trigger.days_offset)
            elif trigger.condition_type == 1:  # On Due Date
                reminder_date = invoice.duedate.date()
            else:  # After Due Date (trigger.condition_type == 2)
                reminder_date = invoice.duedate.date() + timedelta(days=trigger.days_offset)

            # Only include reminders that are today or in the future
            if reminder_date >= today:
                reminders.append({
                    "reminder_date": reminder_date,
                    "trigger_name": trigger.name,
                    "email_subject": trigger.email_subject,
                    "days_until_reminder": (reminder_date - today).days,
                })

        # If reminders exist, return them with the invoice details
        if reminders:
            return Response({
                "invoice_id": invoice.id,
                "invoice_number": invoice.customid,
                "due_date": invoice.duedate.date(),
                "amount_due": invoice.total_amount - invoice.paid_amount,
                "status": invoice.get_status_display(),
                "reminders": sorted(reminders, key=lambda x: x['reminder_date'])
            }, status=status.HTTP_200_OK)
        
        # No future reminders
        return Response({"message": "No future reminders scheduled for this invoice."}, status=status.HTTP_404_NOT_FOUND)

    except Invoices.DoesNotExist:
        return Response({"error": "Invoice not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)








@api_view(['GET'])
def get_all_invoice_reminders(request, invoice_id):
    """
    Retrieve all reminders (including past) for a specified invoice.
    
    This API endpoint provides a complete list of reminders associated with 
    a given invoice based on active email triggers, regardless of whether 
    the reminders are in the past or future. It returns the reminders if 
    the invoice is not fully paid.
    
    Parameters:
    - request: The HTTP request object.
    - invoice_id: The ID of the invoice to check for reminders.
    
    Returns:
    - A response containing all reminders or messages based on the invoice status.
    """

    try:
        # Fetch the invoice for the authenticated user's account
        invoice = Invoices.objects.get(id=invoice_id, account=request.user_account)

        # If the invoice is fully paid, no reminders are needed
        if invoice.status == 2:  # Assuming status 2 is 'Completed' or fully paid
            return Response({"message": "This invoice has been fully paid. No reminders will be sent."}, status=status.HTTP_200_OK)

        # Get all active email triggers for the user's account
        triggers = EmailTrigger.objects.filter(account=request.user_account, isactive=True)

        if not triggers:
            return Response({"message": "No active email triggers found for this account."}, status=status.HTTP_404_NOT_FOUND)

        today = timezone.now().date()
        reminders = []

        # Prepare a dictionary for dynamic formatting
        formatting_data = {
            "invoice_id": invoice.customid,
            "amount_due": invoice.total_amount - invoice.paid_amount,
            "due_date": invoice.duedate.date(),
            "invoice_status": invoice.get_status_display()
        }

        # Loop through each trigger and calculate the reminder dates
        for trigger in triggers:
            if trigger.condition_type == 0:  # Before Due Date
                reminder_date = invoice.duedate.date() - timedelta(days=trigger.days_offset)
            elif trigger.condition_type == 1:  # On Due Date
                reminder_date = invoice.duedate.date()
            else:  # After Due Date (trigger.condition_type == 2)
                reminder_date = invoice.duedate.date() + timedelta(days=trigger.days_offset)

            # Add all reminders regardless of whether they are in the past or future
            email_subject = trigger.email_subject.format(**formatting_data)  # Dynamic fields filled
            
            reminders.append({
                "reminder_date": reminder_date,
                "trigger_name": trigger.name,
                "email_subject": email_subject,
                "days_until_reminder": (reminder_date - today).days,
            })

        # If reminders exist, return them with the invoice details
        return Response({
            "invoice_id": invoice.id,
            "invoice_number": invoice.customid,
            "due_date": invoice.duedate.date(),
            "amount_due": formatting_data["amount_due"],
            "status": formatting_data["invoice_status"],
            "reminders": sorted(reminders, key=lambda x: x['reminder_date'])  # Sorting reminders by date
        }, status=status.HTTP_200_OK)

    except Invoices.DoesNotExist:
        return Response({"error": "Invoice not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






@api_view(['GET'])
def get_invoice_with_all_reminders(request, invoice_id):
    """
    Retrieve reminders for a specified invoice, including only future reminders.
    
    This API endpoint returns future reminders associated with a given invoice 
    based on active email triggers. It also checks if the invoice is fully paid.
    
    Parameters:
    - request: The HTTP request object.
    - invoice_id: The ID of the invoice to check for reminders.
    
    Returns:
    - A response containing future reminders or messages based on the invoice status.
    """
    try:
        # Fetch the invoice for the authenticated user's account
        invoice = Invoices.objects.get(id=invoice_id, account=request.user_account)

        # If the invoice is fully paid, no reminders are needed
        if invoice.status == 2:  # Assuming status 2 is 'Completed' or fully paid
            return Response({"message": "This invoice has been fully paid. No reminders will be sent."}, status=status.HTTP_200_OK)

        # Get all active email triggers for the user's account
        triggers = EmailTrigger.objects.filter(account=request.user_account, isactive=True)

        if not triggers:
            return Response({"message": "No active email triggers found for this account."}, status=status.HTTP_404_NOT_FOUND)

        today = timezone.now().date()
        reminders = []

        # Prepare a dictionary for formatting
        formatting_data = {
            "invoice_id": invoice.customid,
            "amount_due": invoice.total_amount - invoice.paid_amount,
            "due_date": invoice.duedate.date(),
            "invoice_status": invoice.get_status_display()
        }





        # Loop through each trigger and calculate the reminder dates
        for trigger in triggers:
            if trigger.condition_type == 0:  # Before Due Date
                reminder_date = invoice.duedate.date() - timedelta(days=trigger.days_offset)
            elif trigger.condition_type == 1:  # On Due Date
                reminder_date = invoice.duedate.date()
            else:  # After Due Date (trigger.condition_type == 2)
                reminder_date = invoice.duedate.date() + timedelta(days=trigger.days_offset)

            # Only include reminders that are today or in the future
            if reminder_date >= today:
                # Use string formatting to fill in dynamic values
                email_subject = trigger.email_subject.format(**formatting_data)  # Dynamic fields filled
                
                reminders.append({
                    "reminder_date": reminder_date,
                    "trigger_name": trigger.name,
                    "email_subject": email_subject,
                    "days_until_reminder": (reminder_date - today).days,
                })

        # If reminders exist, return them with the invoice details
        if reminders:
            return Response({
                "invoice_id": invoice.id,
                "invoice_number": invoice.customid,
                "due_date": invoice.duedate.date(),
                "amount_due": formatting_data["amount_due"],
                "status": formatting_data["invoice_status"],
                "reminders": sorted(reminders, key=lambda x: x['reminder_date'])
            }, status=status.HTTP_200_OK)
        
        # No future reminders
        return Response({"message": "No future reminders scheduled for this invoice."}, status=status.HTTP_404_NOT_FOUND)

    except Invoices.DoesNotExist:
        return Response({"error": "Invoice not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)







@api_view(['GET'])
def get_account_invoice_reminders(request):
    """
    Retrieve reminders for unpaid or partially paid invoices associated with the user's account.

    Parameters:
        request: The HTTP request object containing user authentication and account information.

    Returns:
        Response: A JSON response containing reminders for invoices, or error messages if applicable.
    """
    try:
        # Authentication check
        if not request.user_is_authenticated:
            return Response({"error": "Authentication failed"}, status=status.HTTP_401_UNAUTHORIZED)
        
        user = request.user_id
        account = request.user_account

        if not account:
            return Response({"error": "User does not have an associated account"}, status=status.HTTP_400_BAD_REQUEST)

        # Get all active email triggers for the account
        triggers = EmailTrigger.objects.filter(account=account, isactive=True)

        if not triggers:
            return Response({"message": "No active email triggers found for this account."}, status=status.HTTP_404_NOT_FOUND)

        # Get all unpaid or partially paid invoices for the account
        invoices = Invoices.objects.filter(account=account, status__in=[0, 1])  # Assuming 0 is Due and 1 is Partial

        today = timezone.now().date()
        reminders = []

        for invoice in invoices:
            invoice_reminders = []
            for trigger in triggers:
                if trigger.condition_type == 0:  # Before Due Date
                    reminder_date = invoice.duedate.date() - timedelta(days=trigger.days_offset)
                elif trigger.condition_type == 1:  # On Due Date
                    reminder_date = invoice.duedate.date()
                elif trigger.condition_type == 2:  # After Due Date
                    reminder_date = invoice.duedate.date() + timedelta(days=trigger.days_offset)

                if reminder_date >= today:
                    invoice_reminders.append({
                        "reminder_date": reminder_date,
                        "trigger_name": trigger.name,
                        "email_subject": trigger.email_subject,
                        "days_until_reminder": (reminder_date - today).days
                    })

            if invoice_reminders:
                reminders.append({
                    "invoice_id": invoice.id,
                    "invoice_number": invoice.customid,
                    "due_date": invoice.duedate.date(),
                    "amount_due": invoice.total_amount - invoice.paid_amount,
                    "status": invoice.get_status_display(),
                    "reminders": sorted(invoice_reminders, key=lambda x: x['reminder_date'])
                })

        if reminders:
            return Response(reminders, status=status.HTTP_200_OK)
        else:
            return Response({"message": "No future reminders scheduled for any invoices."}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    




@api_view(['GET'])
def get_entire_account_invoice_reminders(request):
    """
    Retrieve all reminders for unpaid or partially paid invoices, regardless of their date.

    Parameters:
        request: The HTTP request object containing user authentication and account information.

    Returns:
        Response: A JSON response containing all reminders for invoices, or error messages if applicable.
    """
    try:
        # Authentication check
        if not request.user_is_authenticated:
            return Response({"error": "Authentication failed"}, status=status.HTTP_401_UNAUTHORIZED)
        
        user = request.user_id
        account = request.user_account

        if not account:
            return Response({"error": "User does not have an associated account"}, status=status.HTTP_400_BAD_REQUEST)

        # Get all active email triggers for the account
        triggers = EmailTrigger.objects.filter(account=account, isactive=True)

        if not triggers:
            return Response({"message": "No active email triggers found for this account."}, status=status.HTTP_404_NOT_FOUND)

        # Get all unpaid or partially paid invoices for the account
        invoices = Invoices.objects.filter(account=account, status__in=[0, 1])  # Assuming 0 is Due and 1 is Partial

        today = timezone.now().date()
        reminders = []

        for invoice in invoices:
            invoice_reminders = []
            formatting_data = {
                "invoice_id": invoice.customid,
                "amount_due": invoice.total_amount - invoice.paid_amount,
                "due_date": invoice.duedate.date(),
                "invoice_status": invoice.get_status_display()
            }

            for trigger in triggers:
                if trigger.condition_type == 0:  # Before Due Date
                    reminder_date = invoice.duedate.date() - timedelta(days=trigger.days_offset)
                elif trigger.condition_type == 1:  # On Due Date
                    reminder_date = invoice.duedate.date()
                elif trigger.condition_type == 2:  # After Due Date
                    reminder_date = invoice.duedate.date() + timedelta(days=trigger.days_offset)

                # Create the email subject with dynamic fields
                email_subject = trigger.email_subject.format(**formatting_data)

                # Add all reminders regardless of whether they are in the past or future
                invoice_reminders.append({
                    "reminder_date": reminder_date,
                    "trigger_name": trigger.name,
                    "email_subject": email_subject,
                    "days_until_reminder": (reminder_date - today).days,
                })

            if invoice_reminders:
                reminders.append({
                    "invoice_id": invoice.id,
                    "invoice_number": invoice.customid,
                    "due_date": invoice.duedate.date(),
                    "amount_due": formatting_data["amount_due"],
                    "status": formatting_data["invoice_status"],
                    "reminders": sorted(invoice_reminders, key=lambda x: x['reminder_date'])  # Sorting reminders by date
                })

        if reminders:
            return Response(reminders, status=status.HTTP_200_OK)
        else:
            return Response({"message": "No reminders found for any invoices."}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)