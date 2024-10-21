import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from requests import Response
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from django.shortcuts import get_object_or_404
# Create your views here.
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta

from rest_framework import status
from datetime import timedelta
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum
from .models import Invoices



import pandas as pd


from datetime import timedelta
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum
from .models import Invoices, Payment  # Ensure Payment is imported
from app_cunsole.customer.models import Customers, EmailTrigger
from app_cunsole.customer.serializers import CustomerSerializer
from app_cunsole.invoices.models import DunningPlan
from app_cunsole.invoices.models import Invoices , Payment
from app_cunsole.invoices.serializers import CustomerinvsummarySerializer
from app_cunsole.users.models import Account
from app_cunsole.users.serializers import AccountSerializer
from app_cunsole.users.serializers import UserSerializer
from .serializers import InvoiceWithTriggersSerializer
from .serializers import InvoicedataSerializer, PaymentSerializer, CustomerDueSerializer
from .serializers import InvoiceSerializer
from django.core.mail import send_mail
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from .models import Invoices

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import EmailMessage
import json




@api_view(["POST"])
def create_invoice(request):
    """
    Create a new invoice record.

    This view requires that the user is authenticated. It uses the data from the request to create a new
    invoice record linked to the authenticated user's account. The data is validated and serialized before
    saving the new invoice record.

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

            # Check if customer exists
            customer_id = data.get('customerid')
            if not Customers.objects.filter(id=customer_id).exists():
                return Response(
                    {"error": "Customer ID does not exist"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Initialize serializer
            serializer = InvoiceSerializer(data=data)

            # Validate and save
            if serializer.is_valid():
                invoice = serializer.save()
                return Response(
                    {
                        "success": "Invoice created successfully",
                        "invoice": serializer.data,
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




from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from decimal import Decimal , InvalidOperation
import pandas as pd
from .models import Invoices  # Import your Invoices model
from app_cunsole.customer.models import Account  


@csrf_exempt
def bulk_create_invoices(request):
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

            required_fields = ["customid", "issuedate", "duedate", "name", "customerid", "total_amount"]
            missing_fields = [field for field in required_fields if field not in data.columns]
            if missing_fields:
                return JsonResponse({"error": f"Missing required fields: {', '.join(missing_fields)}"}, status=400)

            invoices_to_create = []
            errors = []

            # Fetch the Account instance
            try:
                account = Account.objects.get(id=account_id)
            except Account.DoesNotExist:
                return JsonResponse({"error": "Invalid account"}, status=400)

            for index, row in data.iterrows():
                try:
                    invoice = Invoices(
                        customid=row["customid"],
                        externalid=row.get("externalid"),
                        issuedate=pd.to_datetime(row["issuedate"]),
                        duedate=pd.to_datetime(row["duedate"]),
                        name=row["name"],
                        currency=row.get("currency", "USD"),
                        total_amount=Decimal(row["total_amount"]),
                        paid_amount=Decimal(row.get("paid_amount", 0)),
                        customerid=row["customerid"],
                        status=row.get("status", 0),  # Default to 'Due' if not provided
                        account=account,
                        user_id=user_id
                    )
                    invoices_to_create.append(invoice)
                except (ValueError, InvalidOperation) as e:
                    errors.append(f"Error in row {index + 2}: {str(e)}")

            if errors:
                return JsonResponse({"error": "Validation errors", "details": errors}, status=400)

            try:
                with transaction.atomic():
                    Invoices.objects.bulk_create(invoices_to_create, batch_size=100)
            except Exception as e:
                return JsonResponse({"error": f"Error creating invoices: {str(e)}"}, status=500)

            return JsonResponse({"success": f"{len(invoices_to_create)} invoices created successfully"})
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



@api_view(["GET"])
# @permission_classes([IsAuthenticated])
def get_invoices_by_account(request):
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

            # Fetch invoices for the user's account using ORM queries (Updated)
            account_invoices = Invoices.objects.filter(account_id=account.id)

            # Serialize the data (Updated)
            serializer = InvoiceSerializer(account_invoices, many=True)

            # Return the response
            return Response({"invoices": serializer.data}, status=status.HTTP_200_OK)

        return Response(
            {"error": "Authentication required"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(["GET"])
def get_customer_invoice_summary(request):
    try:
        # Ensure the user is authenticated
        if request.user_is_authenticated:
            account = request.user_account

            if not account:
                return Response(
                    {"error": "User does not have an associated account"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Fetch all customers based on the account
            customers_list = Customers.objects.filter(account_id=account.id)

            if not customers_list:
                return Response(
                    {"error": "No customers found for the account"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            customer_data = []
            for customer in customers_list:
                customer_invoices = Invoices.objects.filter(customerid=customer.id)
                customer_serializer = CustomerinvsummarySerializer(customer)
                customer_data.append(
                    {
                        "customer": customer_serializer.data,
                        "invoices": InvoicedataSerializer(
                            customer_invoices,
                            many=True,
                        ).data,
                    },
                )

            # Return the response
            return Response(customer_data, status=status.HTTP_200_OK)

        return Response(
            {"error": "Authentication required"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




@api_view(["GET"])
def get_user_account(request):
    if request.user_is_authenticated:
        user = request.user
        try:
            account = Account.objects.get(id=user.Account_id)
        except Account.DoesNotExist:
            return Response(
                {"error": "Account data not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        user_serializer = UserSerializer(user)
        account_serializer = AccountSerializer(account)

        data = {
            "user": user_serializer.data,
            "account": account_serializer.data,
        }
        return Response(data, status=status.HTTP_200_OK)
    else:
        return Response(
            {"error": "Authentication credentials were not provided."},
            status=status.HTTP_401_UNAUTHORIZED,
        )



# @csrf_exempt
def send_email_view(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            subject = data.get("subject")
            message = data.get("message")
            from_email = data.get("from_email")
            recipient_list = data.get("recipient_list", [])

            email = EmailMessage(
                subject,
                message,
                from_email,
                recipient_list,
            )
            email.content_subtype = "html"  # If sending HTML email
            email.send(fail_silently=False)
            return JsonResponse({"status": "success", "message": "Email sent successfully"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)




# @csrf_exempt
@api_view(["GET"])
def get_customer_summary(request, customer_id):
    try:
        # Ensure the user is authenticated
        if request.user_is_authenticated:
            account = request.user_account

            if not account:
                return Response(
                    {"error": "User does not have an associated account"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Fetch the specific customer based on the customer_id and account_id
            try:
                customer = Customers.objects.get(id=customer_id, account_id=account.id)
            except Customers.DoesNotExist:
                return Response(
                    {"error": "Customer not found for the account"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Fetch all invoices associated with the customer
            customer_invoices = Invoices.objects.filter(customerid=customer.id)

            # Serialize the customer and invoice data
            customer_serializer = CustomerSerializer(customer)
            invoices_serializer = InvoicedataSerializer(customer_invoices, many=True)

            # Prepare the response data
            response_data = {
                "customer": customer_serializer.data,
                "invoices": invoices_serializer.data,
            }

            # Return the response
            return Response(response_data, status=status.HTTP_200_OK)

        return Response(
            {"error": "Authentication required"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





# @api_view(['POST'])
# def add_payment(request):
#     """
#     API view to add a payment entry and update the corresponding invoice.
#     """
#     # Ensure the user is authenticated
#     if not request.user_is_authenticated:
#         return Response({"detail": "Authentication credentials were not provided."}, status=status.HTTP_401_UNAUTHORIZED)

#     # Get the user's associated account
#     account = request.user_account
#     if not account:
#         return Response(
#             {"error": "User does not have an associated account"},
#             status=status.HTTP_400_BAD_REQUEST,
#         )
    
#     # Initialize and validate the payment serializer
#     payment_serializer = PaymentSerializer(data=request.data)
    
#     if payment_serializer.is_valid():
#         # Extract the invoice ID and payment amount from validated data
#         invoice_id = payment_serializer.validated_data['invoice']
#         amount = payment_serializer.validated_data['amount']
        
#         try:
#             # Retrieve the invoice based on the provided ID
#             invoice = Invoices.objects.get(id=invoice_id)
            
#             # Calculate the remaining amount on the invoice
#             remaining_amount = invoice.total_amount - invoice.paid_amount
            
#             # Check if the payment amount exceeds the remaining balance
#             if amount > remaining_amount:
#                 return Response(
#                     {"detail": "Payment amount exceeds the remaining balance of the invoice."},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )
            
#             # Save the payment entry with the extracted account ID and user ID
#             payment = payment_serializer.save(account=account)
            
#             # Update the paid amount on the invoice
#             new_paid_amount = invoice.paid_amount + amount
            
#             # Determine the new status of the invoice based on the paid amount
#             if new_paid_amount >= invoice.total_amount:
#                 invoice.status = Invoices.STATUS_CHOICES[2][0]  # Completed
#             elif new_paid_amount > 0:
#                 invoice.status = Invoices.STATUS_CHOICES[1][0]  # Partial
#             else:
#                 invoice.status = Invoices.STATUS_CHOICES[0][0]  # Due

#             invoice.paid_amount = new_paid_amount
#             invoice.save()

#             # Serialize and return the updated invoice
#             updated_invoice_serializer = InvoiceSerializer(invoice)
#             return Response(updated_invoice_serializer.data, status=status.HTTP_201_CREATED)
        
#         except Invoices.DoesNotExist:
#             # Return error if the invoice does not exist
#             return Response(
#                 {"detail": "Invoice not found."},
#                 status=status.HTTP_404_NOT_FOUND
#             )
    
#     # Return validation errors if serializer is not valid
#     return Response(payment_serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# current api
# @api_view(["POST"])
# def add_payment(request):
#     """
#     Create a new payment record.

#     This view requires that the user is authenticated. It uses the data from the request to create a new
#     payment record linked to the authenticated user's account and the specified invoice. The data is validated
#     and serialized before saving the new payment record.

#     Returns:
#         Response: A JSON response indicating the result of the creation attempt.
#                   If authentication is not provided, returns a 401 Unauthorized error.
#                   If the data is invalid, returns a 400 Bad Request error.
#     """
#     try:
#         if request.user_is_authenticated:  # Check if the user is authenticated
#             user = request.user_id  # Get the authenticated user's ID from the middleware
#             account = request.user_account  # Get the associated account from the middleware

#             if not account:
#                 return Response(
#                     {"error": "User does not have an associated account"},
#                     status=status.HTTP_400_BAD_REQUEST,
#                 )

#             # Deserialize the request data
#             data = request.data.copy()
#             data['user'] = user  # Assign the authenticated user ID
#             data['account'] = account.id  # Assign the account ID from the user
            
#             # Get the invoice ID from the request data and validate
#             invoice_id = data.get('invoice')
#             try:
#                 invoice = Invoices.objects.get(id=invoice_id)
#             except Invoices.DoesNotExist:
#                 return Response(
#                     {"error": "Invoice not found"},
#                     status=status.HTTP_404_NOT_FOUND,
#                 )
            
#             # Set the invoice for the payment
#             data['invoice'] = invoice.id

#             # Initialize serializer
#             serializer = PaymentSerializer(data=data)

#             # Validate and save
#             if serializer.is_valid():
#                 payment = serializer.save()
#                 return Response(
#                     {
#                         "success": "Payment created successfully",
#                         "payment": serializer.data,
#                     },
#                     status=status.HTTP_201_CREATED,
#                 )

#             # Log validation errors
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         return Response(
#             {"error": "Authentication required"},
#             status=status.HTTP_401_UNAUTHORIZED,
#         )

#     except Exception as e:
#         return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
def add_payment(request):
    """
    Create a new payment record and update the related invoice.

    Returns:
        Response: A JSON response with payment and invoice status.
    """
    try:
        if not request.user_is_authenticated:
            return Response(
                {"error": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user = request.user_id  # Authenticated user's ID
        account = request.user_account  # User's associated account

        if not account:
            return Response(
                {"error": "User does not have an associated account"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Deserialize request data
        data = request.data.copy()
        data['user'] = user
        data['account'] = account.id

        # Retrieve and validate the invoice
        invoice_id = data.get('invoice')
        try:
            invoice = Invoices.objects.get(id=invoice_id)
        except Invoices.DoesNotExist:
            return Response(
                {"error": "Invoice not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Validate the new payment amount before saving
        payment_amount = data.get('amount')
        if payment_amount is None or float(payment_amount) <= 0:
            return Response(
                {"error": "Invalid payment amount."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_paid_amount = invoice.paid_amount + Decimal(payment_amount)

        # Ensure no overpayment
        if new_paid_amount > invoice.total_amount:
            return Response(
                {"error": "Payment exceeds the invoice total amount."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Initialize the serializer after validation
        serializer = PaymentSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Save the payment only after validation
        payment = serializer.save()

        # Update the invoice with the new paid amount and status
        invoice.paid_amount = new_paid_amount

        # Determine the new status of the invoice
        if invoice.paid_amount == 0:
            invoice.status = 0  # Due
        elif invoice.paid_amount < invoice.total_amount:
            invoice.status = 1  # Partial
        else:
            invoice.status = 2  # Completed

        invoice.save()  # Save the updated invoice

        return Response(
            {
                "success": "Payment created successfully and invoice updated.",
                "payment": serializer.data,
                "invoice_status": invoice.get_status_display(),
            },
            status=status.HTTP_201_CREATED,
        )

    except Exception as e:
        return Response(
            {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



# @csrf_exempt
@api_view(['GET'])
def get_customer_payments(request, customer_id):
    """
    Retrieve all payments made by a specific customer associated with the authenticated user's account.

    This view requires that the user is authenticated. It fetches payments that are linked
    to the customer's invoices under the authenticated user's account. The data is serialized
    and returned in the response.

    Returns:
        Response: A JSON response containing the list of payments and a status code.
                  If authentication is not provided or the customer is not found, returns
                  an appropriate error response.
    """
    if request.user_is_authenticated:
        # Retrieve the authenticated user
        user = request.user

        # Retrieve the account associated with the authenticated user
        account = request.user_account

        try:
            # Ensure the customer exists and belongs to the user's account
            customer = Customers.objects.get(id=customer_id, account=account)
            
            # Retrieve all payments linked to the customer's invoices
            payments = Payment.objects.filter(invoice__customerid=customer.id, account=account)
            
            # Serialize the payment data
            serializer = PaymentSerializer(payments, many=True)
            
            # Return the serialized data with a 200 OK status
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Customers.DoesNotExist:
            # Return error if the customer does not exist or does not belong to the user's account
            return Response(
                {"detail": "Customer not found or does not belong to your account."},
                status=status.HTTP_404_NOT_FOUND
            )
    
    else:
        # If the user is not authenticated, return a 401 Unauthorized error
        return Response(
            {"error": "Authentication credentials were not provided."},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    


@api_view(['GET'])
def invoice_details(request, invoice_id):
    try:
        # Check if the user is authenticated
        if not request.user_is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Retrieve the invoice details
        invoice = Invoices.objects.get(pk=invoice_id)
        customer = Customers.objects.get(id=invoice.customerid)
        payments = Payment.objects.filter(invoice=invoice)

        # Serialize the data
        invoice_data = InvoiceSerializer(invoice).data
        customer_data = CustomerinvsummarySerializer(customer).data
        payment_data = PaymentSerializer(payments, many=True).data

        # Combine the data into a single response
        response_data = {
            "invoice": invoice_data,
            "customer": customer_data,
            "payments": payment_data
        }

        return Response(response_data, status=status.HTTP_200_OK)
    
    except Invoices.DoesNotExist:
        return Response({"error": "Invoice not found"}, status=status.HTTP_404_NOT_FOUND)
    except Customers.DoesNotExist:
        return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)
    







from .serializers import InvoiceWithTriggersSerializer

@api_view(['GET'])
def check_email_trigger(request, invoice_id):
    try:
        invoice = Invoices.objects.get(id=invoice_id)
    except Invoices.DoesNotExist:
        return Response({'error': 'Invoice not found'}, status=404)

    triggers = EmailTrigger.objects.filter(account=invoice.account, isactive=True)
    active_triggers = []

    for trigger in triggers:
        condition_date = {
            0: invoice.duedate - timedelta(days=trigger.days_offset),
            1: invoice.duedate,
            2: invoice.duedate + timedelta(days=trigger.days_offset)
        }.get(trigger.condition_type, invoice.duedate)

        if timezone.now() >= condition_date:
            active_triggers.append({
                'trigger_id': trigger.id,
                'trigger_name': trigger.name,
                'condition_type': trigger.get_condition_type_display(),
                'email_subject': trigger.email_subject,
                'email_body': trigger.email_body,
                'trigger_date': condition_date
            })

    return Response({'invoice_id': invoice_id, 'active_triggers': active_triggers})



def format_email_content(template, context):
    """
    Replace placeholders in the email template with actual data.
    """
    for key, value in context.items():
        placeholder = f'{{{{ {key} }}}}'
        if placeholder in template:
            template = template.replace(placeholder, str(value))
        else:
            print(f"Placeholder {placeholder} not found in template.")
    return template

@api_view(['GET'])
def check_email_trigger(request, invoice_id):
    try:
        invoice = Invoices.objects.get(id=invoice_id)
    except Invoices.DoesNotExist:
        return JsonResponse({'error': 'Invoice not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    try:
        serializer = InvoiceWithTriggersSerializer(invoice)
        invoice_data = serializer.data
    except Exception as e:
        return JsonResponse({'error': f'Error serializing invoice: {str(e)}'}, status=500)

    triggers = EmailTrigger.objects.filter(account=invoice.account, isactive=True)
    active_triggers = []

    for trigger in triggers:
        try:
            if trigger.condition_type == 0:  # Reminder before due
                trigger_date = invoice.duedate - timedelta(days=trigger.days_offset)
            elif trigger.condition_type == 1:  # Reminder on due
                trigger_date = invoice.duedate
            elif trigger.condition_type == 2:  # Reminder after due
                trigger_date = invoice.duedate + timedelta(days=trigger.days_offset)
            else:
                trigger_date = invoice.duedate  # Default case

            next_alert_date = trigger_date if timezone.now() >= trigger_date else None

            try:
                customer = Customers.objects.get(id=invoice.customerid)
            except Customers.DoesNotExist:
                return JsonResponse({'error': f'Customer with ID {invoice.customerid} not found'}, status=404)

            context = {
                'invoice_id': invoice.customid,
                'name': customer.name,
                'status': invoice.get_status_display(),
                'amount_due': invoice.total_amount - invoice.paid_amount
            }

            email_subject = format_email_content(trigger.email_subject, context)
            email_body = format_email_content(trigger.email_body, context)

            # Debug output
            print(f"Original Email Subject: {trigger.email_subject}")
            print(f"Formatted Email Subject: {email_subject}")
            print(f"Original Email Body: {trigger.email_body}")
            print(f"Formatted Email Body: {email_body}")

            active_triggers.append({
                'trigger_id': trigger.id,
                'trigger_name': trigger.name,
                'condition_type': trigger.get_condition_type_display(),
                'email_subject': email_subject,
                'email_body': email_body,
                'trigger_date': trigger_date,
                'next_alert_date': next_alert_date
            })

        except Exception as e:
            return JsonResponse({'error': f'Error processing trigger: {str(e)}'}, status=500)

    return JsonResponse({'invoice': invoice_data, 'active_triggers': active_triggers})








# views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum, F, Q
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from .models import Invoices, Payment
from .serializers import InvoiceSerializer, PaymentSerializer

from django.db.models import Sum, F, Avg  # Add Avg to the import





# @api_view(["GET"])
# def invoice_summary_cards(request):
#     try:
#         # Ensure the user is authenticated
#         if request.user_is_authenticated:
#             user = request.user
#             account = request.user_account

#             if not account:
#                 return Response(
#                     {"error": "User does not have an associated account"},
#                     status=status.HTTP_400_BAD_REQUEST,
#                 )

#             # Get current date and date one month ago
#             current_date = timezone.now().date()
#             one_month_ago = current_date - relativedelta(months=1)
            
#             # Base queryset
#             invoices = Invoices.objects.filter(account_id=account.id)
            
#             # Calculate current month's metrics
#             current_outstanding = invoices.filter(
#                 status__in=[0, 1],
#                 issuedate__lte=current_date
#             ).aggregate(total=Sum(F('total_amount') - F('paid_amount')))['total'] or 0
            
#             current_overdue = invoices.filter(
#                 status__in=[0, 1],
#                 duedate__lt=current_date
#             ).aggregate(total=Sum(F('total_amount') - F('paid_amount')))['total'] or 0
            
#             current_due = invoices.filter(
#                 status=0,
#                 issuedate__lte=current_date
#             ).aggregate(total=Sum(F('total_amount') - F('paid_amount')))['total'] or 0
            
#             # Calculate last month's metrics
#             last_month_outstanding = invoices.filter(
#                 status__in=[0, 1],
#                 issuedate__lte=one_month_ago
#             ).aggregate(total=Sum(F('total_amount') - F('paid_amount')))['total'] or 0
            
#             last_month_overdue = invoices.filter(
#                 status__in=[0, 1],
#                 duedate__lt=one_month_ago
#             ).aggregate(total=Sum(F('total_amount') - F('paid_amount')))['total'] or 0
            
#             last_month_due = invoices.filter(
#                 status=0,
#                 issuedate__lte=one_month_ago
#             ).aggregate(total=Sum(F('total_amount') - F('paid_amount')))['total'] or 0
            
#             # Calculate percentage changes
#             def calculate_percentage_change(current, previous):
#                 if previous == 0:
#                     return 100 if current > 0 else 0
#                 return ((current - previous) / previous) * 100

#             outstanding_change = calculate_percentage_change(current_outstanding, last_month_outstanding)
#             overdue_change = calculate_percentage_change(current_overdue, last_month_overdue)
#             due_change = calculate_percentage_change(current_due, last_month_due)
            
#             # Prepare the response data
#             summary = {
#                 'outstanding': {
#                     'current': current_outstanding,
#                     'previous': last_month_outstanding,
#                     'change': round(outstanding_change, 2),
#                 },
#                 'overdue': {
#                     'current': current_overdue,
#                     'previous': last_month_overdue,
#                     'change': round(overdue_change, 2),
#                 },
#                 'due': {
#                     'current': current_due,
#                     'previous': last_month_due,
#                     'change': round(due_change, 2),
#                 },
#             }
            
#             return Response({
#                 'summary': summary,
#             }, status=status.HTTP_200_OK)

#         return Response(
#             {"error": "Authentication required"},
#             status=status.HTTP_401_UNAUTHORIZED,
#         )

#     except Exception as e:
#         return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(["GET"])
def invoice_summary_cards(request):
    try:
        # Ensure the user is authenticated
        if request.user_is_authenticated:
            user = request.user
            account = request.user_account

            if not account:
                return Response(
                    {"error": "User does not have an associated account"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get current date and date one month ago
            current_date = timezone.now().date()
            one_month_ago = current_date - timedelta(days=30)

            # Base queryset filtered by account
            invoices = Invoices.objects.filter(account=account)

            # Calculate total receivables
            total_receivables = invoices.aggregate(
                total=Sum(F('total_amount') - F('paid_amount'))
            )['total'] or 0

            # Calculate overdue amount
            overdue_amount = invoices.filter(
                duedate__lt=current_date, status__in=[0, 1]
            ).aggregate(total=Sum(F('total_amount') - F('paid_amount')))['total'] or 0

            # Calculate due amount (future or today)
            due_amount = invoices.filter(
                duedate__gte=current_date, status__in=[0, 1]
            ).aggregate(total=Sum(F('total_amount') - F('paid_amount')))['total'] or 0

            # Calculate last month overdue
            last_month_overdue = invoices.filter(
                duedate__lt=one_month_ago, status__in=[0, 1]
            ).aggregate(total=Sum(F('total_amount') - F('paid_amount')))['total'] or 0

            # Calculate last month due
            last_month_due = invoices.filter(
                duedate__gte=one_month_ago, status__in=[0, 1]
            ).aggregate(total=Sum(F('total_amount') - F('paid_amount')))['total'] or 0

            # Calculate outstanding
            current_outstanding = total_receivables
            last_month_outstanding = invoices.filter(
                status__in=[0, 1], issuedate__lte=one_month_ago
            ).aggregate(total=Sum(F('total_amount') - F('paid_amount')))['total'] or 0

            # Helper to calculate percentage changes
            def calculate_percentage_change(current, previous):
                if previous == 0:
                    return 100 if current > 0 else 0
                return ((current - previous) / previous) * 100

            # Prepare the response summary
            summary = {
                'outstanding': {
                    'current': current_outstanding,
                    'previous': last_month_outstanding,
                    'change': round(calculate_percentage_change(current_outstanding, last_month_outstanding), 2),
                },
                'overdue': {
                    'current': overdue_amount,
                    'previous': last_month_overdue,
                    'change': round(calculate_percentage_change(overdue_amount, last_month_overdue), 2),
                },
                'due': {
                    'current': due_amount,
                    'previous': last_month_due,
                    'change': round(calculate_percentage_change(due_amount, last_month_due), 2),
                },
            }

            return Response({'summary': summary}, status=status.HTTP_200_OK)

        return Response(
            {"error": "Authentication required"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
def dso_data_card(request):
    try:
        if request.user_is_authenticated:
            account = request.user_account

            if not account:
                return Response(
                    {"error": "User does not have an associated account"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get date range from query parameters
            start_date_str = request.query_params.get('start_date')
            end_date_str = request.query_params.get('end_date')
            
            # If no dates provided, default to last 6 months
            if not start_date_str or not end_date_str:
                end_date = timezone.now().date().replace(day=1)
                start_date = (end_date - relativedelta(months=5)).replace(day=1)
            else:
                try:
                    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                except ValueError:
                    return Response(
                        {"error": "Invalid date format. Use YYYY-MM-DD."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            monthly_dso = []
            current_date = start_date
            
            while current_date <= end_date:
                month_end = (current_date + relativedelta(months=1) - relativedelta(days=1))
                
                # Calculate total sales for the month
                total_sales = Invoices.objects.filter(
                    account_id=account.id,
                    issuedate__range=[current_date, month_end]
                ).aggregate(total=Sum('total_amount'))['total'] or 0
                
                # Calculate average accounts receivable for the month
                avg_receivables = Invoices.objects.filter(
                    account_id=account.id,
                    issuedate__lte=month_end,
                    status__in=[0, 1]  # Assuming 0 and 1 are statuses for unpaid invoices
                ).aggregate(avg=Avg(F('total_amount') - F('paid_amount')))['avg'] or 0
                
                # Calculate DSO
                dso = (avg_receivables / total_sales * 30) if total_sales > 0 else 0
                
                monthly_dso.append({
                    'month': current_date.strftime('%b %Y'),
                    'dso': round(dso, 1)
                })

                current_date += relativedelta(months=1)

            if len(monthly_dso) >= 2:
                current_dso = monthly_dso[-1]['dso']
                previous_dso = monthly_dso[-2]['dso']
                percentage_change = ((current_dso - previous_dso) / previous_dso * 100) if previous_dso > 0 else 0
            else:
                current_dso = monthly_dso[-1]['dso'] if monthly_dso else 0
                previous_dso = 0
                percentage_change = 0

            average_dso = sum(item['dso'] for item in monthly_dso) / len(monthly_dso) if monthly_dso else 0

            return Response({
                'dso_data': monthly_dso,
                'current_dso': current_dso,
                'previous_dso': previous_dso,
                'percentage_change': round(percentage_change, 2),
                'average_dso': round(average_dso, 1)
            }, status=status.HTTP_200_OK)

        return Response(
            {"error": "Authentication required"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





# views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum, F
from django.utils import timezone
from datetime import timedelta
from .models import Invoices

@api_view(['GET'])
def ar_status_card(request):
    try:
        # Ensure the user is authenticated
        if request.user_is_authenticated:
            user = request.user
            account = request.user_account

            if not account:
                return Response(
                    {"error": "User does not have an associated account"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get current date and date one month ago
            current_date = timezone.now().date()
            one_month_ago = current_date - timedelta(days=30)

            # Base queryset filtered by account
            invoices = Invoices.objects.filter(account=account)

            # Calculate total receivables
            total_receivables = invoices.aggregate(
                total=Sum(F('total_amount') - F('paid_amount'))
            )['total'] or 0

            # Calculate overdue amount
            overdue_invoices = invoices.filter(duedate__lt=current_date, status__in=[0, 1])
            overdue_amount = overdue_invoices.aggregate(
                overdue=Sum(F('total_amount') - F('paid_amount'))
            )['overdue'] or 0

            # Calculate overdue percentage
            overdue_percentage = (overdue_amount / total_receivables * 100) if total_receivables > 0 else 0

            # Calculate aging buckets
            aging_data = [
                {
                    'name': 'Due',
                    'value': invoices.filter(duedate__gte=current_date, status__in=[0, 1]).aggregate(
                        due=Sum(F('total_amount') - F('paid_amount'))
                    )['due'] or 0,
                    'color': '#10b981',
                    'category': 'due'
                },
                {
                    'name': 'Overdue',
                    'value': overdue_amount,
                    'color': '#ef4444',
                    'category': 'overdue'
                },
                {
                    'name': '1-30 days',
                    'value': overdue_invoices.filter(duedate__gte=current_date - timedelta(days=30)).aggregate(
                        amount=Sum(F('total_amount') - F('paid_amount'))
                    )['amount'] or 0,
                    'color': '#eab308',
                    'category': 'aging'
                },
                {
                    'name': '31-60 days',
                    'value': overdue_invoices.filter(duedate__range=[current_date - timedelta(days=60), current_date - timedelta(days=31)]).aggregate(
                        amount=Sum(F('total_amount') - F('paid_amount'))
                    )['amount'] or 0,
                    'color': '#f97316',
                    'category': 'aging'
                },
                {
                    'name': '61-90 days',
                    'value': overdue_invoices.filter(duedate__range=[current_date - timedelta(days=90), current_date - timedelta(days=61)]).aggregate(
                        amount=Sum(F('total_amount') - F('paid_amount'))
                    )['amount'] or 0,
                    'color': '#ec4899',
                    'category': 'aging'
                },
                {
                    'name': '> 90 days',
                    'value': overdue_invoices.filter(duedate__lt=current_date - timedelta(days=90)).aggregate(
                        amount=Sum(F('total_amount') - F('paid_amount'))
                    )['amount'] or 0,
                    'color': '#7c3aed',
                    'category': 'aging'
                },
            ]

            # Calculate summary cards data
            def calculate_percentage_change(current, previous):
                if previous == 0:
                    return 100 if current > 0 else 0
                return ((current - previous) / previous) * 100

            current_outstanding = total_receivables
            last_month_outstanding = invoices.filter(
                status__in=[0, 1],
                issuedate__lte=one_month_ago
            ).aggregate(total=Sum(F('total_amount') - F('paid_amount')))['total'] or 0

            current_due = invoices.filter(
                status=0,
                issuedate__lte=current_date
            ).aggregate(total=Sum(F('total_amount') - F('paid_amount')))['total'] or 0
            last_month_due = invoices.filter(
                status=0,
                issuedate__lte=one_month_ago
            ).aggregate(total=Sum(F('total_amount') - F('paid_amount')))['total'] or 0

            summary = {
                'outstanding': {
                    'current': current_outstanding,
                    'previous': last_month_outstanding,
                    'change': round(calculate_percentage_change(current_outstanding, last_month_outstanding), 2),
                },
                'overdue': {
                    'current': overdue_amount,
                    'previous': invoices.filter(
                        status__in=[0, 1],
                        duedate__lt=one_month_ago
                    ).aggregate(total=Sum(F('total_amount') - F('paid_amount')))['total'] or 0,
                    'change': round(calculate_percentage_change(overdue_amount, invoices.filter(
                        status__in=[0, 1],
                        duedate__lt=one_month_ago
                    ).aggregate(total=Sum(F('total_amount') - F('paid_amount')))['total'] or 0), 2),
                },
                'due': {
                    'current': current_due,
                    'previous': last_month_due,
                    'change': round(calculate_percentage_change(current_due, last_month_due), 2),
                },
            }

            response_data = {
                'total_receivables': total_receivables,
                'overdue_percentage': overdue_percentage,
                'aging_data': aging_data,
                'summary': summary,
            }

            return Response(response_data, status=status.HTTP_200_OK)

        return Response(
            {"error": "Authentication required"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    



# @api_view(['GET'])
# # @permission_classes([IsAuthenticated])  # Ensure the user is authenticated
# def get_top_due_customers(request):
#     """
#     API to get top due customers for a user's account with due amounts and days left for due.
#     It calculates the due amount by summing all unpaid invoices and the number of days to the closest due date.
#     """
#     # Step 1: Get the authenticated user's account
#     # user = request.user
#     # account = user.account  # Assuming 'account' is a related field in the User model

#     # if not account:
#     #     return Response(
#     #         {"error": "User does not have an associated account"},
#     #         status=status.HTTP_400_BAD_REQUEST,
#     #     )

#     try:
#         # Ensure the user is authenticated
#         if request.user_is_authenticated:
#             user = request.user
#             account = request.user_account

#             if not account:
#                 return Response(
#                     {"error": "User does not have an associated account"},
#                     status=status.HTTP_400_BAD_REQUEST,
#                 )

#     # Step 2: Query for customers associated with the account
#     customers = Customers.objects.filter(account=account)

#     # Step 3: List to hold processed customer data
#     top_due_customers = []

#     # Step 4: Process each customer to calculate the total due amount and due days
#     for customer in customers:
#         # Get all unpaid invoices for the customer (status=0 means 'Due')
#         unpaid_invoices = Invoices.objects.filter(customerid=customer.id, status=0)

#         # Skip if no unpaid invoices for this customer
#         if not unpaid_invoices.exists():
#             continue

#         # Calculate the total due amount for the customer
#         total_due_amount = unpaid_invoices.aggregate(total_due=Sum('total_amount'))['total_due'] or 0

#         # Calculate the nearest due date (oldest 'duedate' from unpaid invoices)
#         nearest_due_invoice = unpaid_invoices.order_by('duedate').first()
#         nearest_due_date = nearest_due_invoice.duedate if nearest_due_invoice else None

#         # Calculate the number of days until due (or overdue if negative)
#         if nearest_due_date:
#             due_in_days = (nearest_due_date - timezone.now()).days
#         else:
#             due_in_days = None

#         # Prepare customer data
#         customer_data = {
#             'name': customer.name,
#             'due': f'{total_due_amount:,.2f}',  # Format as comma-separated number with two decimals
#             'dueIn': f'{due_in_days} days' if due_in_days is not None else 'N/A'
#         }

#         # Append to the top due customer list
#         top_due_customers.append(customer_data)

#     # Step 5: Sort customers by the highest due amount (descending)
#     top_due_customers.sort(key=lambda x: float(x['due'].replace(',', '')), reverse=True)

#     # Step 6: Return the top due customers as JSON response
#     return Response(top_due_customers)


# card

# @api_view(['GET'])
# def get_top_due_customers(request):
#     """
#     API to get top due customers for a user's account with due amounts and days left for due.
#     It calculates the due amount by summing all unpaid invoices and the number of days to the closest due date.
#     """
#     try:
#         # Ensure the user is authenticated
#         if request.user_is_authenticated:
#             user = request.user
#             account = request.user_account  # Assuming 'user_account' is set correctly

#             if not account:
#                 return Response(
#                     {"error": "User does not have an associated account"},
#                     status=status.HTTP_400_BAD_REQUEST,
#                 )

#             # Query for customers associated with the account
#             customers = Customers.objects.filter(account=account)

#             # List to hold processed customer data
#             top_due_customers = []

#             # Process each customer to calculate the total due amount and due days
#             for customer in customers:
#                 # Get all unpaid invoices for the customer (status=0 means 'Due')
#                 unpaid_invoices = Invoices.objects.filter(customerid=customer.id, status__in=[0, 1])

#                 # Skip if no unpaid invoices for this customer
#                 if not unpaid_invoices.exists():
#                     continue

#                 # Calculate the total due amount for the customer
#                 total_due_amount = unpaid_invoices.aggregate(total_due=Sum('total_amount'))['total_due'] or 0

#                 # Calculate the nearest due date (oldest 'duedate' from unpaid invoices)
#                 nearest_due_invoice = unpaid_invoices.order_by('duedate').first()
#                 nearest_due_date = nearest_due_invoice.duedate if nearest_due_invoice else None

#                 # Calculate the number of days until due (or overdue if negative)
#                 if nearest_due_date:
#                     due_in_days = (nearest_due_date - timezone.now()).days
#                 else:
#                     due_in_days = None

#                 # Prepare customer data
#                 customer_data = {
#                     'name': customer.name,
#                     'due': f'{total_due_amount:,.2f}',  # Format as comma-separated number with two decimals
#                     'dueIn': f'{due_in_days} days' if due_in_days is not None else 'N/A'
#                 }

#                 # Append to the top due customer list
#                 top_due_customers.append(customer_data)

#             # Sort customers by the highest due amount (descending)
#             top_due_customers.sort(key=lambda x: float(x['due'].replace(',', '')), reverse=True)

#             # Return the top due customers as JSON response
#             return Response(top_due_customers)

#         return Response(
#             {"error": "Authentication required"},
#             status=status.HTTP_401_UNAUTHORIZED,
#         )

#     except Exception as e:
#         return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['GET'])
def get_top_due_customers(request):
    """
    API to get top due customers for a user's account with due amounts and days left for due.
    It calculates the due amount by summing the outstanding amount of unpaid and partially paid invoices.
    """
    try:
        # Ensure the user is authenticated
        if request.user_is_authenticated:
            user = request.user
            account = request.user_account  # Ensure 'user_account' is correctly set

            if not account:
                return Response(
                    {"error": "User does not have an associated account"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Query for customers associated with the account
            customers = Customers.objects.filter(account=account)

            # List to hold processed customer data
            top_due_customers = []

            # Process each customer to calculate the total outstanding amount and due days
            for customer in customers:
                # Get all unpaid or partially paid invoices (status 0 or 1) for the customer
                unpaid_invoices = Invoices.objects.filter(customerid=customer.id, status__in=[0, 1])

                # Skip if no unpaid or partially paid invoices exist for this customer
                if not unpaid_invoices.exists():
                    continue

                # Calculate the total outstanding amount (total_amount - paid_amount)
                total_outstanding = unpaid_invoices.aggregate(
                    total_due=Sum(F('total_amount') - F('paid_amount'))
                )['total_due'] or 0

                # Get the nearest due date (earliest 'duedate' among unpaid invoices)
                nearest_due_invoice = unpaid_invoices.order_by('duedate').first()
                nearest_due_date = nearest_due_invoice.duedate if nearest_due_invoice else None

                # Calculate the number of days until due (or overdue if negative)
                if nearest_due_date:
                    due_in_days = (nearest_due_date.date() - timezone.now().date()).days
                else:
                    due_in_days = None

                # Prepare the customer data
                customer_data = {
                    'name': customer.name,
                    'due': f'{total_outstanding:,.2f}',  # Format as comma-separated with two decimals
                    'dueIn': f'{due_in_days} days' if due_in_days is not None else 'N/A'
                }

                # Append to the top due customers list
                top_due_customers.append(customer_data)

            # Sort customers by the highest outstanding amount in descending order
            top_due_customers.sort(key=lambda x: float(x['due'].replace(',', '')), reverse=True)

            # Return the top due customers as JSON response
            return Response(top_due_customers, status=status.HTTP_200_OK)

        # Handle unauthenticated access
        return Response(
            {"error": "Authentication required"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta

from rest_framework import status
from datetime import timedelta
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum
from .models import Invoices



from datetime import timedelta
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum
from .models import Invoices, Payment  # Ensure Payment is imported

@api_view(['GET'])
def invoice_payment_card(request):
    """
    API to get issued invoices and collected payments by date range
    or the last month if no range is provided.
    """
    try:
        # Ensure the user is authenticated
        if request.user_is_authenticated:
            user = request.user
            account = request.user_account  # Assuming 'user_account' is set correctly

            if not account:
                return Response(
                    {"error": "User does not have an associated account"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get the current date
            today = timezone.now()
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')

            # If no date range is provided, set the date range to the last month
            if not start_date or not end_date:
                end_date = today
                start_date = today - timedelta(days=30)  # Last month
            else:
                # Convert string date to datetime
                start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d')
                end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d')

            # Query for invoices issued within the specified date range for the user's account
            invoices = Invoices.objects.filter(
                account=account,
                issuedate__range=[start_date, end_date]
            ).values('id', 'issuedate', 'total_amount')  # Collecting required fields

            # Query for payments collected within the specified date range
            payments = Payment.objects.filter(
                account=account,
                payment_date__range=[start_date, end_date]
            ).values('id', 'amount', 'payment_date')  # Collecting required fields

            # Prepare data for response
            invoice_data = list(invoices)
            payment_data = list(payments)

            # Return the response with separate lists for invoices and payments
            return Response({
                "invoices": invoice_data,
                "payments": payment_data
            }, status=status.HTTP_200_OK)

        return Response(
            {"error": "Authentication required"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    




from datetime import datetime
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.db.models import Sum
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Invoices



# @api_view(["GET"])
# def credit_sales_card_data(request):
#     try:
#         if request.user_is_authenticated:
#             account = request.user_account

#             if not account:
#                 return Response(
#                     {"error": "User does not have an associated account"},
#                     status=status.HTTP_400_BAD_REQUEST,
#                 )

#             # Get date range from query parameters
#             start_date_str = request.query_params.get('start_date')
#             end_date_str = request.query_params.get('end_date')
            
#             # If no dates provided, default to last 12 months
#             if not start_date_str or not end_date_str:
#                 end_date = timezone.now().date()
#                 start_date = end_date - relativedelta(months=11)
#             else:
#                 try:
#                     start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
#                     end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
#                 except ValueError:
#                     return Response(
#                         {"error": "Invalid date format. Use YYYY-MM-DD."},
#                         status=status.HTTP_400_BAD_REQUEST,
#                     )

#             monthly_data = []
#             current_date = start_date
            
#             while current_date <= end_date:
#                 month_end = (current_date + relativedelta(months=1) - relativedelta(days=1))
                
#                 # Fetching invoices for the current month
#                 invoices = Invoices.objects.filter(
#                     account_id=account.id,
#                     issuedate__range=[current_date, month_end],
#                     status__in=[0, 1]  # Assuming 0 and 1 are statuses for unpaid invoices
#                 )

#                 # Calculate total credit sales for the month
#                 total_credit_sales = invoices.aggregate(total=Sum('total_amount'))['total'] or 0

#                 # Calculate within due and overdue amounts
#                 within_due = invoices.filter(
#                     duedate__gte=timezone.now()
#                 ).aggregate(total=Sum('total_amount'))['total'] or 0
                
#                 overdue = invoices.filter(
#                     duedate__lt=timezone.now()
#                 ).aggregate(total=Sum('total_amount'))['total'] or 0

#                 # Collect invoice details
#                 invoice_details = [
#                     {
#                         'id': invoice.id,  # Include the invoice ID
#                         'customid': invoice.customid,
#                         'name': invoice.name,
#                         'issuedate': invoice.issuedate,
#                         'total_amount': invoice.total_amount,
#                         'paid_amount': invoice.paid_amount,
#                         'status': invoice.get_status_display()  # Get display value for status
#                     }
#                     for invoice in invoices
#                 ]

#                 monthly_data.append({
#                     'month': current_date.strftime('%b'),
#                     'totalCreditSale': total_credit_sales,
#                     'withinDue': within_due,
#                     'overdue': overdue,
#                     'invoices': invoice_details  # Include invoice details in the response
#                 })

#                 current_date += relativedelta(months=1)

#             return Response({
#                 'data': monthly_data
#             }, status=status.HTTP_200_OK)

#         return Response(
#             {"error": "Authentication required"},
#             status=status.HTTP_401_UNAUTHORIZED,
#         )

#     except Exception as e:
#         return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# @api_view(["GET"])
# def credit_sales_card_data(request):
#     try:
#         if request.user_is_authenticated:
#             account = request.user_account

#             if not account:
#                 return Response(
#                     {"error": "User does not have an associated account"},
#                     status=status.HTTP_400_BAD_REQUEST,
#                 )

#             # Get date range from query parameters
#             start_date_str = request.query_params.get('start_date')
#             end_date_str = request.query_params.get('end_date')
            
#             # If no dates provided, default to last 12 months
#             if not start_date_str or not end_date_str:
#                 end_date = timezone.now().date()
#                 start_date = end_date - relativedelta(months=11)
#             else:
#                 try:
#                     start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
#                     end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
#                 except ValueError:
#                     return Response(
#                         {"error": "Invalid date format. Use YYYY-MM-DD."},
#                         status=status.HTTP_400_BAD_REQUEST,
#                     )

#             monthly_data = []
#             current_date = start_date
            
#             while current_date <= end_date:
#                 month_end = (current_date + relativedelta(months=1) - relativedelta(days=1))
                
#                 # Fetching invoices for the current month
#                 invoices = Invoices.objects.filter(
#                     account_id=account.id,
#                     issuedate__range=[current_date, month_end],
#                     status__in=[0, 1]  # Assuming 0 and 1 are statuses for unpaid invoices
#                 )

#                 # Calculate total credit sales for the month
#                 total_credit_sales = invoices.aggregate(total=Sum('total_amount'))['total'] or 0

#                 # Calculate within due and overdue amounts
#                 within_due = invoices.filter(
#                     duedate__gte=timezone.now()
#                 ).aggregate(total=Sum('total_amount'))['total'] or 0
                
#                 overdue = invoices.filter(
#                     duedate__lt=timezone.now()
#                 ).aggregate(total=Sum('total_amount'))['total'] or 0

#                 # Collect invoice details
#                 invoice_details = [
#                     {
#                         'id': invoice.id,  # Include the invoice ID
#                         'customid': invoice.customid,
#                         'name': invoice.name,
#                         'issuedate': invoice.issuedate.isoformat(),  # Standard ISO format
#                         'total_amount': invoice.total_amount,
#                         'paid_amount': invoice.paid_amount,
#                         'status': invoice.get_status_display()  # Get display value for status
#                     }
#                     for invoice in invoices
#                 ]

#                 monthly_data.append({
#                     'month_start': current_date.isoformat(),  # Start of the month in ISO format
#                     'month_end': month_end.isoformat(),  # End of the month in ISO format
#                     'totalCreditSale': total_credit_sales,
#                     'withinDue': within_due,
#                     'overdue': overdue,
#                     'invoices': invoice_details  # Include invoice details in the response
#                 })

#                 current_date += relativedelta(months=1)

#             return Response({
#                 'data': monthly_data
#             }, status=status.HTTP_200_OK)

#         return Response(
#             {"error": "Authentication required"},
#             status=status.HTTP_401_UNAUTHORIZED,
#         )

#     except Exception as e:
#         return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    


# @api_view(["GET"])
# def credit_sales_card_data(request):
#     try:
#         if request.user_is_authenticated:
#             account = request.user_account

#             if not account:
#                 return Response(
#                     {"error": "User does not have an associated account"},
#                     status=status.HTTP_400_BAD_REQUEST,
#                 )

#             # Get start_date and end_date from query parameters
#             start_date_str = request.query_params.get('start_date', None)
#             end_date_str = request.query_params.get('end_date', None)

#             # Validate and parse date formats
#             try:
#                 if start_date_str:
#                     start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
#                 else:
#                     start_date = timezone.now().date() - timedelta(days=30)  # Default to the last 30 days

#                 if end_date_str:
#                     end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
#                 else:
#                     end_date = timezone.now().date()
#             except ValueError:
#                 return Response(
#                     {"error": "Invalid date format. Use YYYY-MM-DD."},
#                     status=status.HTTP_400_BAD_REQUEST,
#                 )

#             # Fetch invoices within the specified date range
#             invoices = Invoices.objects.filter(
#                 account_id=account.id,
#                 issuedate__range=(start_date, end_date)
#             )

#             # Prepare daily aggregated data
#             daily_data = []
#             current_date = start_date

#             while current_date <= end_date:
#                 daily_invoices = invoices.filter(issuedate=current_date)

#                 total_credits = daily_invoices.aggregate(total=Sum('total_amount'))['total'] or 0
#                 within_due = daily_invoices.filter(duedate__gte=timezone.now()).aggregate(total=Sum('total_amount'))['total'] or 0
#                 overdue = daily_invoices.filter(duedate__lt=timezone.now()).aggregate(total=Sum('total_amount'))['total'] or 0

#                 daily_data.append({
#                     "date": current_date,
#                     "total_credits": total_credits,
#                     "within_due": within_due,
#                     "overdue": overdue,
#                     "invoices": [
#                         {
#                             "id": invoice.id,
#                             "customid": invoice.customid,
#                             "name": invoice.name,
#                             "issuedate": invoice.issuedate,
#                             "total_amount": invoice.total_amount,
#                             "paid_amount": invoice.paid_amount,
#                             "status": invoice.get_status_display(),
#                         }
#                         for invoice in daily_invoices
#                     ]
#                 })
#                 current_date += timedelta(days=1)

#             return Response({"data": daily_data}, status=status.HTTP_200_OK)

#         return Response(
#             {"error": "Authentication required"},
#             status=status.HTTP_401_UNAUTHORIZED,
#         )

#     except Exception as e:
#         return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        




# @api_view(["GET"])
# def credit_sales_card_data(request):



#     try:
        
#         if request.user_is_authenticated:
#             account = request.user_account

#             if not account:
#                 return Response(
#                     {"error": "User does not have an associated account"},
#                     status=status.HTTP_400_BAD_REQUEST,
#                 )

#             # Get issuedate from query parameters
#             issuedate_str = request.query_params.get('issuedate')

#             if issuedate_str:
#                 try:
#                     issuedate = datetime.strptime(issuedate_str, '%Y-%m-%d').date()
#                 except ValueError:
#                     return Response(
#                         {"error": "Invalid date format. Use YYYY-MM-DD."},
#                         status=status.HTTP_400_BAD_REQUEST,
#                     )
                
#                 # Filter invoices by the issued date
#                 invoices = Invoices.objects.filter(
#                     account_id=account.id,
#                     issuedate=issuedate,
#                     status__in=[0, 1]  # Assuming 0 and 1 are statuses for unpaid invoices
#                 )

#                 invoice_details = [
#                     {
#                         'id': invoice.id,
#                         'customid': invoice.customid,
#                         'name': invoice.name,
#                         'issuedate': invoice.issuedate.isoformat(),
#                         'total_amount': invoice.total_amount,
#                         'paid_amount': invoice.paid_amount,
#                         'status': invoice.get_status_display()  # Get display value for status
#                     }
#                     for invoice in invoices
#                 ]

#                 # Calculate within due and overdue amounts for the specified issued date
#                 within_due = invoices.filter(
#                     duedate__gte=timezone.now()
#                 ).aggregate(total=Sum('total_amount'))['total'] or 0
                
#                 overdue = invoices.filter(
#                     duedate__lt=timezone.now()
#                 ).aggregate(total=Sum('total_amount'))['total'] or 0

#                 return Response({
#                     'issuedate': issuedate.isoformat(),
#                     'invoices': invoice_details,
#                     'withinDue': within_due,
#                     'overdue': overdue
#                 }, status=status.HTTP_200_OK)

#             # If no issuedate is provided, return monthly data for the last 12 months
#             end_date = timezone.now().date()
#             start_date = end_date - relativedelta(months=11)

#             monthly_data = []
#             current_date = start_date
            
#             while current_date <= end_date:
#                 month_end = (current_date + relativedelta(months=1) - relativedelta(days=1))

#                 # Fetching invoices for the current month
#                 invoices = Invoices.objects.filter(
#                     account_id=account.id,
#                     issuedate__range=[current_date, month_end],
#                     status__in=[0, 1]  # Assuming 0 and 1 are statuses for unpaid invoices
#                 )

#                 # Calculate total credit sales for the month
#                 total_credit_sales = invoices.aggregate(total=Sum('total_amount'))['total'] or 0

#                 # Calculate within due and overdue amounts for the month
#                 within_due = invoices.filter(
#                     duedate__gte=timezone.now()
#                 ).aggregate(total=Sum('total_amount'))['total'] or 0
                
#                 overdue = invoices.filter(
#                     duedate__lt=timezone.now()
#                 ).aggregate(total=Sum('total_amount'))['total'] or 0

#                 # Collect invoice details
#                 invoice_details = [
#                     {
#                         'id': invoice.id,
#                         'customid': invoice.customid,
#                         'name': invoice.name,
#                         'issuedate': invoice.issuedate.isoformat(),
#                         'total_amount': invoice.total_amount,
#                         'paid_amount': invoice.paid_amount,
#                         'status': invoice.get_status_display()  # Get display value for status
#                     }
#                     for invoice in invoices
#                 ]

#                 monthly_data.append({
#                     'month_start': current_date.isoformat(),
#                     'month_end': month_end.isoformat(),
#                     'totalCreditSale': total_credit_sales,
#                     'withinDue': within_due,
#                     'overdue': overdue,
#                     'invoices': invoice_details  # Include invoice details in the response
#                 })

#                 current_date += relativedelta(months=1)

#             # Fill in any months without data
#             while current_date <= end_date:
#                 month_end = (current_date + relativedelta(months=1) - relativedelta(days=1))
#                 monthly_data.append({
#                     'month_start': current_date.isoformat(),
#                     'month_end': month_end.isoformat(),
#                     'totalCreditSale': 0,
#                     'withinDue': 0,
#                     'overdue': 0,
#                     'invoices': []
#                 })
#                 current_date += relativedelta(months=1)

#             return Response({
#                 'data': monthly_data
#             }, status=status.HTTP_200_OK)

#         return Response(
#             {"error": "Authentication required"},
#             status=status.HTTP_401_UNAUTHORIZED,
#         )

#     except Exception as e:
#         return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(["GET"])
def credit_sales_card_data(request):
    try:
        if request.user_is_authenticated:
            account = request.user_account

            if not account:
                return Response(
                    {"error": "User does not have an associated account"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get start_date and end_date from query parameters
            start_date_str = request.query_params.get('start_date')
            end_date_str = request.query_params.get('end_date')

            if start_date_str and end_date_str:
                try:
                    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                except ValueError:
                    return Response(
                        {"error": "Invalid date format. Use YYYY-MM-DD."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                
                # Filter invoices by the date range
                invoices = Invoices.objects.filter(
                    account_id=account.id,
                    issuedate__range=[start_date, end_date],
                    status__in=[0, 1]  # Assuming 0 and 1 are statuses for unpaid invoices
                )

                invoice_details = [
                    {
                        'id': invoice.id,
                        'customid': invoice.customid,
                        'name': invoice.name,
                        'issuedate': invoice.issuedate.isoformat(),
                        'total_amount': invoice.total_amount,
                        'paid_amount': invoice.paid_amount,
                        'status': invoice.get_status_display()
                    }
                    for invoice in invoices
                ]

                # Calculate totals for the entire date range
                total_credit_sales = invoices.aggregate(total=Sum('total_amount'))['total'] or 0
                within_due = invoices.filter(
                    duedate__gte=timezone.now()
                ).aggregate(total=Sum('total_amount'))['total'] or 0
                overdue = invoices.filter(
                    duedate__lt=timezone.now()
                ).aggregate(total=Sum('total_amount'))['total'] or 0

                return Response({
                    'data': [{
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat(),
                        'totalCreditSale': total_credit_sales,
                        'withinDue': within_due,
                        'overdue': overdue,
                        'invoices': invoice_details
                    }]
                }, status=status.HTTP_200_OK)

            # If no date range is provided, return monthly data for the last 12 months
            end_date = timezone.now().date()
            start_date = end_date - relativedelta(months=11)

            monthly_data = []
            current_date = start_date
            
            while current_date <= end_date:
                month_end = (current_date + relativedelta(months=1) - relativedelta(days=1))

                # Fetching invoices for the current month
                invoices = Invoices.objects.filter(
                    account_id=account.id,
                    issuedate__range=[current_date, month_end],
                    status__in=[0, 1]
                )

                total_credit_sales = invoices.aggregate(total=Sum('total_amount'))['total'] or 0
                within_due = invoices.filter(
                    duedate__gte=timezone.now()
                ).aggregate(total=Sum('total_amount'))['total'] or 0
                overdue = invoices.filter(
                    duedate__lt=timezone.now()
                ).aggregate(total=Sum('total_amount'))['total'] or 0

                invoice_details = [
                    {
                        'id': invoice.id,
                        'customid': invoice.customid,
                        'name': invoice.name,
                        'issuedate': invoice.issuedate.isoformat(),
                        'total_amount': invoice.total_amount,
                        'paid_amount': invoice.paid_amount,
                        'status': invoice.get_status_display()
                    }
                    for invoice in invoices
                ]

                monthly_data.append({
                    'start_date': current_date.isoformat(),
                    'end_date': month_end.isoformat(),
                    'totalCreditSale': total_credit_sales,
                    'withinDue': within_due,
                    'overdue': overdue,
                    'invoices': invoice_details
                })

                current_date += relativedelta(months=1)

            return Response({
                'data': monthly_data
            }, status=status.HTTP_200_OK)

        return Response(
            {"error": "Authentication required"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

