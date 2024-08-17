import json

import jwt
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from app_cunsole.customer.models import Customers
from app_cunsole.users.models import User

from .serializers import CustomerSerializer

from django.shortcuts import render, get_object_or_404
from django.core.mail import send_mail
from django.utils import timezone
from django.http import JsonResponse
from app_cunsole.invoices.models import Invoices

from .models import  EmailTrigger, Customers
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import EmailTrigger
from .serializers import EmailTriggerSerializer
from django.views.decorators.csrf import csrf_exempt





# Create your views here.
@csrf_exempt
def create_customer(request):
    if request.method == "POST":
        # Retrieve JWT token from Authorization header
        header = request.headers.get("Authorization")

        if header and header.startswith("Bearer "):
            token = header.split(" ")[1]

            try:
                # Decode the JWT token
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
                user_id = payload["user_id"]

                # Fetch the user and their account
                user = User.objects.get(id=user_id)
                account = user.Account

                # Deserialize the request data
                data = json.loads(request.body)

                # Add user and account to the request data
                data["user"] = user_id
                data["account"] = account.id if account else None

                serializer = CustomerSerializer(data=data)

                if serializer.is_valid():
                    # Save the customer instance
                    customer = serializer.save()
                    return JsonResponse(
                        {
                            "success": "Customer created successfully",
                            "customer": serializer.data,
                        },
                        status=201,
                    )
                else:
                    return JsonResponse(
                        {"error": "Invalid data", "details": serializer.errors},
                        status=400,
                    )

            except jwt.ExpiredSignatureError:
                return JsonResponse({"error": "Token is expired"}, status=401)
            except jwt.InvalidTokenError:
                return JsonResponse({"error": "Invalid token"}, status=401)
            except User.DoesNotExist:
                return JsonResponse({"error": "User not found"}, status=401)

        return JsonResponse(
            {"error": "Authorization header format is invalid"},
            status=401,
        )

    return JsonResponse({"error": "Method not allowed."}, status=405)




# bulk create customers api
@csrf_exempt
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






@csrf_exempt
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
            data = request.data.copy()
            data['user'] = user.id
            data['account'] = account.id


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



@csrf_exempt
@api_view(["GET"])
def get_email_triggers(request):
    """
    Retrieve all active email triggers for the authenticated user and their associated account.

    This view requires that the user is authenticated. It fetches email triggers that are linked
    to the authenticated user's account and are marked as active. The data is serialized and returned
    in the response.

    Returns:
        Response: A JSON response containing the list of email triggers and a status code.
                  If authentication is not provided, returns a 401 Unauthorized error.
    """
    if request.user_is_authenticated:
        # Retrieve the authenticated user
        user = request.user

        # Retrieve the account associated with the authenticated user
        account = request.user_account

        # Filter email triggers based on the user, their account, and active status
        email_triggers = EmailTrigger.objects.filter(user=user, account=account, isactive=True)

        # Serialize the email triggers
        serializer = EmailTriggerSerializer(email_triggers, many=True)

        # Return the serialized data with a 200 OK status
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        # If the user is not authenticated, return a 401 Unauthorized error
        return Response(
            {"error": "Authentication credentials were not provided."},
            status=status.HTTP_401_UNAUTHORIZED,
        )





@csrf_exempt
def send_reminders(request):
    if request.method == 'POST':
        # Get today's date
        today = timezone.now().date()

        # Retrieve all active email triggers
        triggers = EmailTrigger.objects.filter(isactive=True)

        # Prepare a list to collect emails sent and related invoice details
        sent_emails_info = []

        # Iterate over each active email trigger
        for trigger in triggers:
            # Determine the target date based on the trigger condition type
            if trigger.condition_type == 0:  # Before Due Date
                target_date = today + timezone.timedelta(days=trigger.days_offset)
            elif trigger.condition_type == 1:  # On Due Date
                target_date = today
            elif trigger.condition_type == 2:  # After Due Date
                target_date = today - timezone.timedelta(days=trigger.days_offset)
            else:
                # Skip this trigger if the condition type is not recognized
                continue

            # Find invoices that match the target date and account associated with the trigger
            invoices = Invoices.objects.filter(duedate=target_date, account=trigger.account)

            # Iterate over each invoice
            for invoice in invoices:
                # Find the customer associated with the invoice
                customer = Customers.objects.filter(id=invoice.customerid).first()

                # Send an email if the customer has an email address
                if customer and customer.email:
                    send_email(
                        to_email=customer.email,
                        subject=trigger.email_subject,
                        body=trigger.email_body.format(
                            name=customer.name,  # Customer's name
                            invoice_id=invoice.customid,  # Invoice ID
                            amount_due=invoice.total_amount - invoice.paid_amount,  # Amount due
                        )
                    )

                    # Collect email and invoice details
                    sent_emails_info.append({
                        "customer_email": customer.email,
                        "customer_name": customer.name,
                        "invoice_id": invoice.customid,
                        "amount_due": invoice.total_amount - invoice.paid_amount,
                    })

        # Return a JSON response indicating success with email and invoice details
        return JsonResponse({
            "status": "Reminders sent successfully",
            "sent_emails_info": sent_emails_info
        })
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)



@csrf_exempt
def send_email(to_email, subject, body):
    """
    Send an email to the specified address.

    Parameters:
    - to_email (str): The recipient's email address
    - subject (str): The subject of the email
    - body (str): The body content of the email
    """
    send_mail(
        subject,
        body,
        'from@example.com',  # Change this to your sender email
        [to_email],
        fail_silently=False,
    )
