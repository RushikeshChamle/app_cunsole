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

from app_cunsole.customer.models import Customers
from app_cunsole.customer.serializers import CustomerSerializer
from app_cunsole.invoices.models import DunningPlan
from app_cunsole.invoices.models import Invoices , Payment
from app_cunsole.invoices.serializers import CustomerinvsummarySerializer
from app_cunsole.users.models import Account
from app_cunsole.users.serializers import AccountSerializer
from app_cunsole.users.serializers import UserSerializer

from .serializers import InvoicedataSerializer, PaymentSerializer
from .serializers import InvoiceSerializer
from django.core.mail import send_mail
from django.http import HttpResponse
from django.conf import settings

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import EmailMessage
import json


@csrf_exempt
def create_invoice(request):
    if request.method == "POST":
        if request.user_is_authenticated:
            account = request.user_account

            # Deserialize request data
            data = json.loads(request.body)
            data["account"] = account.id if account else None

            # Validate customer and dunning plan if provided
            customer_id = data.get("customerid")
            if customer_id and not Customers.objects.filter(id=customer_id).exists():
                return JsonResponse({"error": "Customer not found"}, status=400)

            dunningplan_id = data.get("dunningplan")
            if (
                dunningplan_id
                and not DunningPlan.objects.filter(id=dunningplan_id).exists()
            ):
                return JsonResponse({"error": "Dunning Plan not found"}, status=400)
            # Save the invoice
            serializer = InvoiceSerializer(data=data)
            if serializer.is_valid():
                invoice = serializer.save()
                return JsonResponse(
                    {
                        "success": "Invoice created successfully",
                        "invoice": serializer.data,
                    },
                    status=201,
                )
            else:
                return JsonResponse(
                    {"error": "Invalid data", "details": serializer.errors},
                    status=400,
                )
        else:
            return JsonResponse({"error": "Authentication required"}, status=401)
    else:
        return JsonResponse({"error": "Method not allowed."}, status=405)



def bulk_create_invoices(request):
    if request.method == "POST":
        # Check if the user is authenticated (Updated)
        if request.user_is_authenticated:
            user = request.user
            account = request.user_account

            # Handle file upload
            if "file" not in request.FILES:
                return JsonResponse({"error": "No file provided"}, status=400)

            file = request.FILES["file"]

            # Check file extension and read the file into a DataFrame (Updated)
            if file.name.endswith(".csv"):
                df = pd.read_csv(file)
            elif file.name.endswith(".xlsx"):
                df = pd.read_excel(file)
            else:
                return JsonResponse({"error": "Unsupported file format"}, status=400)

            # Prepare to collect valid invoice data
            invoices_data = []

            # Validate and process each row (Updated)
            for index, row in df.iterrows():
                data = {
                    "customid": row.get("customid"),
                    "externalid": row.get("externalid"),
                    "issuedat": row.get("issuedat"),
                    "duedate": row.get("duedate"),
                    "name": row.get("name"),
                    "currency": row.get("currency"),
                    "grossamount": row.get("grossamount"),
                    "netamount": row.get("netamount"),
                    "account": account.id if account else None,
                    "customerid": row.get("customerid"),
                }

                # Validate customer if provided (Updated)
                if (
                    data.get("customerid")
                    and not Customers.objects.filter(id=data["customerid"]).exists()
                ):
                    return JsonResponse(
                        {"error": f'Customer {data["customerid"]} not found'},
                        status=400,
                    )

                # Serialize data (Updated)
                serializer = InvoiceSerializer(data=data)
                if serializer.is_valid():
                    invoices_data.append(serializer.validated_data)
                else:
                    return JsonResponse(
                        {"error": "Invalid data", "details": serializer.errors},
                        status=400,
                    )

            # Bulk create invoices (Updated)
            if invoices_data:
                invoice_instances = [Invoices(**data) for data in invoices_data]
                Invoices.objects.bulk_create(invoice_instances)

            return JsonResponse(
                {"success": "Invoices created successfully"},
                status=201,
            )

        else:
            return JsonResponse({"error": "Authentication required"}, status=401)

    return JsonResponse({"error": "Method not allowed."}, status=405)



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



@csrf_exempt
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
        if request.user.is_authenticated:
            account = request.user.account

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





@api_view(['POST'])
def add_payment(request):
    """
    API view to add a payment entry and update the corresponding invoice.
    """
    # Ensure the user is authenticated
    if not request.user_is_authenticated:
        return Response({"detail": "Authentication credentials were not provided."}, status=status.HTTP_401_UNAUTHORIZED)

    # Get the user's associated account
    account = request.user_account
    if not account:
        return Response(
            {"error": "User does not have an associated account"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    
    # Initialize and validate the payment serializer
    payment_serializer = PaymentSerializer(data=request.data)
    
    if payment_serializer.is_valid():
        # Extract the invoice ID and payment amount from validated data
        invoice_id = payment_serializer.validated_data['invoice']
        amount = payment_serializer.validated_data['amount']
        
        try:
            # Retrieve the invoice based on the provided ID
            invoice = Invoices.objects.get(id=invoice_id)
            
            # Calculate the remaining amount on the invoice
            remaining_amount = invoice.total_amount - invoice.paid_amount
            
            # Check if the payment amount exceeds the remaining balance
            if amount > remaining_amount:
                return Response(
                    {"detail": "Payment amount exceeds the remaining balance of the invoice."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Save the payment entry with the extracted account ID and user ID
            payment = payment_serializer.save(account=account)
            
            # Update the paid amount on the invoice
            new_paid_amount = invoice.paid_amount + amount
            
            # Determine the new status of the invoice based on the paid amount
            if new_paid_amount >= invoice.total_amount:
                invoice.status = Invoices.STATUS_CHOICES[2][0]  # Completed
            elif new_paid_amount > 0:
                invoice.status = Invoices.STATUS_CHOICES[1][0]  # Partial
            else:
                invoice.status = Invoices.STATUS_CHOICES[0][0]  # Due

            invoice.paid_amount = new_paid_amount
            invoice.save()

            # Serialize and return the updated invoice
            updated_invoice_serializer = InvoiceSerializer(invoice)
            return Response(updated_invoice_serializer.data, status=status.HTTP_201_CREATED)
        
        except Invoices.DoesNotExist:
            # Return error if the invoice does not exist
            return Response(
                {"detail": "Invoice not found."},
                status=status.HTTP_404_NOT_FOUND
            )
    
    # Return validation errors if serializer is not valid
    return Response(payment_serializer.errors, status=status.HTTP_400_BAD_REQUEST)




@csrf_exempt
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
        if not request.user.is_authenticated:
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