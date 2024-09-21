import json

import jwt
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes

from rest_framework.permissions import IsAuthenticated
from app_cunsole.customer.models import Customers
from app_cunsole.users.models import User
from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from .serializers import CustomerSerializer
import uuid
from django.core.mail import EmailMessage

from app_cunsole.invoices.models import Invoices
from django.shortcuts import render, get_object_or_404
from django.core.mail import send_mail
from django.utils import timezone
from django.http import JsonResponse

from .models import  EmailTrigger, Customers
from django.views import View

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import EmailTrigger
from .serializers import EmailTriggerSerializer
from django.views.decorators.csrf import csrf_exempt





# # Create your views here.
# def create_customer(request):
#     if request.method == "POST":
#         # Retrieve JWT token from Authorization header
#         header = request.headers.get("Authorization")

#         if header and header.startswith("Bearer "):
#             token = header.split(" ")[1]

#             try:
#                 # Decode the JWT token
#                 payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
#                 user_id = payload["user_id"]

#                 # Fetch the user and their account
#                 user = User.objects.get(id=user_id)
#                 account = user.Account

#                 # Deserialize the request data
#                 data = json.loads(request.body)

#                 # Add user and account to the request data
#                 data["user"] = user_id
#                 data["account"] = account.id if account else None

#                 serializer = CustomerSerializer(data=data)

#                 if serializer.is_valid():
#                     # Save the customer instance
#                     customer = serializer.save()
#                     return JsonResponse(
#                         {
#                             "success": "Customer created successfully",
#                             "customer": serializer.data,
#                         },
#                         status=201,
#                     )
#                 else:
#                     return JsonResponse(
#                         {"error": "Invalid data", "details": serializer.errors},
#                         status=400,
#                     )

#             except jwt.ExpiredSignatureError:
#                 return JsonResponse({"error": "Token is expired"}, status=401)
#             except jwt.InvalidTokenError:
#                 return JsonResponse({"error": "Invalid token"}, status=401)
#             except User.DoesNotExist:
#                 return JsonResponse({"error": "User not found"}, status=401)

#         return JsonResponse(
#             {"error": "Authorization header format is invalid"},
#             status=401,
#         )

#     return JsonResponse({"error": "Method not allowed."}, status=405)



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
    if request.user_is_authenticated:
        try:
            # Deserialize the request data
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=status.HTTP_400_BAD_REQUEST)

        # Add user and account to the request data
        data["user"] = request.user.id
        data["account"] = request.user_account.id if request.user_account else None

        # Serialize and validate the data
        serializer = CustomerSerializer(data=data)

        if serializer.is_valid():
            # Save the customer instance
            customer = serializer.save()
            return JsonResponse(
                {
                    "success": "Customer created successfully",
                    "customer": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )
        else:
            return JsonResponse(
                {"error": "Invalid data", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
    else:
        return JsonResponse(
            {"error": "Authentication credentials were not provided."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

# bulk create customers api

def bulk_create_customers(request):
    if request.method == "POST":
        # Check if the Authorization header is present
        header = request.headers.get("Authorization")
        if header and header.startswith("Bearer "):
            token = header.split(" ")[1]

            try:
                # Decode the JWT token
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
                user_id = payload["user_id"]
                user = User.objects.get(id=user_id)
            except jwt.ExpiredSignatureError:
                return JsonResponse({"error": "Token is expired"}, status=401)
            except jwt.InvalidTokenError:
                return JsonResponse({"error": "Invalid token"}, status=401)
            except User.DoesNotExist:
                return JsonResponse({"error": "User not found"}, status=401)

            # Check if a file was uploaded
            if "file" not in request.FILES:
                return JsonResponse({"error": "No file uploaded"}, status=400)

            file = request.FILES["file"]

            # Check file type
            if not file.name.endswith(".csv") and not file.name.endswith(".xlsx"):
                return JsonResponse(
                    {
                        "error": "Unsupported file type. Please upload a CSV or Excel file.",
                    },
                    status=400,
                )

            # Read file
            try:
                if file.name.endswith(".csv"):
                    data = pd.read_csv(file)
                elif file.name.endswith(".xlsx"):
                    data = pd.read_excel(file)
            except Exception as e:
                return JsonResponse({"error": str(e)}, status=400)

            # Process data
            customers_to_create = []
            for index, row in data.iterrows():
                customer = Customers(
                    externalid=row["externalid"],
                    name=row["name"],
                    email=row["email"],
                    phone=row["phone"],
                    address=row["address"],
                    city=row["city"],
                    state=row["state"],
                    country=row["country"],
                    postalcode=row["postalcode"],
                    taxid=row["taxid"],
                    companyname=row["companyname"],
                    industrytype=row["industrytype"],
                    paymentterms=row["paymentterms"],
                    creditlimit=row["creditlimit"],
                    notes=row["notes"],
                    isactive=row["isactive"],
                    account=user.Account,  # Associate with the user's account
                    user=user,  # Associate with the user who is making the request
                )
                customers_to_create.append(customer)

            # Bulk create customers
            if customers_to_create:
                Customers.objects.bulk_create(customers_to_create)

            return JsonResponse({"success": "Customers created successfully"})

        return JsonResponse(
            {"error": "Authorization header format is invalid"},
            status=401,
        )

    return JsonResponse({"error": "Method not allowed."}, status=405)







@api_view(["POST"])
def create_email_trigger(request):
    """
    Handle POST requests to create a new EmailTrigger record.

    - Ensures the user is authenticated.
    - Associates the EmailTrigger with the authenticated user and their account.
    - Validates and saves the new EmailTrigger record.
    - Returns appropriate responses based on the request outcome.
    """
    try:
        # Check if the user is authenticated
        if request.user_is_authenticated:
            user = request.user
            account = request.user_account

            # Verify that the user has an associated account
            if not account:
              return Response(
                  {"error": "User does not have an associated account"},
                  status=status.HTTP_400_BAD_REQUEST,
            )

            # Prepare data for serializer by including user and account information
            data = request.data
            data.update({'user': user.id, 'account': account.id})



            # Initialize the serializer with the provided data
            serializer = EmailTriggerSerializer(data=data)

            # Validate and save the data if valid
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            # Return validation errors if any
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Return an error if the user is not authenticated
        return Response(
            {"error": "Authentication required"},
            status=status.HTTP_401_UNAUTHORIZED,

        )
    
    except Exception as e:
        # Return a server error response in case of unexpected exceptions
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




# @api_view(["GET"])
# def get_email_triggers(request):
#     """
#     Retrieve all active email triggers for the authenticated user and their associated account.

#     This view requires that the user is authenticated. It fetches email triggers that are linked
#     to the authenticated user's account and are marked as active. The data is serialized and returned
#     in the response.

#     Returns:
#         Response: A JSON response containing the list of email triggers and a status code.
#                   If authentication is not provided, returns a 401 Unauthorized error.
#     """
#     if request.user_is_authenticated:
#         # Retrieve the authenticated user
#         user = request.user

#         # Retrieve the account associated with the authenticated user
#         account = request.user_account

#         # Filter email triggers based on the user, their account, and active status
#         email_triggers = EmailTrigger.objects.filter(user=user, account=account, isactive=True)

#         # Serialize the email triggers
#         serializer = EmailTriggerSerializer(email_triggers, many=True)

#         # Return the serialized data with a 200 OK status
#         return Response(serializer.data, status=status.HTTP_200_OK)
#     else:
#         # If the user is not authenticated, return a 401 Unauthorized error
#         return Response(
#             {"error": "Authentication credentials were not provided."},
#             status=status.HTTP_401_UNAUTHORIZED,
#         )

import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import EmailTrigger
from .serializers import EmailTriggerSerializer

logger = logging.getLogger(__name__)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_email_triggers_by_account(request):
    try:
        user = request.user
        if not user.is_authenticated:
            return Response(
                {"error": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        account = getattr(user, 'account', None)
        if not account:
            return Response(
                {"error": "User does not have an associated account"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email_triggers = EmailTrigger.objects.filter(account=account)
        serializer = EmailTriggerSerializer(email_triggers, many=True)
        
        return Response({"email_triggers": serializer.data}, status=status.HTTP_200_OK)

    except EmailTrigger.DoesNotExist:
        logger.warning(f"No email triggers found for account {account.id}")
        return Response({"email_triggers": []}, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error in get_email_triggers_by_account: {str(e)}")
        return Response(
            {"error": "An unexpected error occurred"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


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
    if request.user.is_authenticated:
        try:
            # Retrieve the authenticated user
            user = request.user

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
@permission_classes([IsAuthenticated])
def get_customers_by_account(request):
    try:
        # Ensure the user is authenticated (Updated)
        if request.user_is_authenticated:
            user = request.user
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



@shared_task
def send_reminders_emails_task():
    today = timezone.now().date()
    triggers = EmailTrigger.objects.filter(isactive=True)
    sent_emails_info = []

    for trigger in triggers:
        if trigger.condition_type == 0:  # Before Due Date
            target_date = today + timezone.timedelta(days=trigger.days_offset)
        elif trigger.condition_type == 1:  # On Due Date
            target_date = today
        elif trigger.condition_type == 2:  # After Due Date
            target_date = today - timezone.timedelta(days=trigger.days_offset)
        else:
            continue

        invoices = Invoices.objects.filter(
            duedate=target_date,
            status__in=[0, 1],  # Due or Partial
            account=trigger.account
        )

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

                # Send the email asynchronously
                send_email_task.delay(customer.email, subject, body)

                sent_emails_info.append({
                    "customer_email": customer.email,
                    "customer_name": customer.name,
                    "invoice_id": invoice.customid,
                    "amount_due": invoice.total_amount - invoice.paid_amount,
                })

    return sent_emails_info




@shared_task
def send_email_task(to_email, subject, body):
    send_mail(
        subject,
        body,
        'info@cunsole.com',  # Change this to your sender email
        [to_email],
        fail_silently=False,
    )



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

        # Send the test email asynchronously
        send_email_task.delay(test_email, subject, body)

        return Response({
            "status": "Test email task initiated",
            "email_subject": subject,
            "email_body": body
        })

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)