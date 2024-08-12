import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from requests import Response
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes

# Create your views here.
from rest_framework.permissions import IsAuthenticated

from app_cunsole.customer.models import Customers
from app_cunsole.customer.serializers import CustomerSerializer
from app_cunsole.invoices.models import DunningPlan
from app_cunsole.invoices.models import Invoices
from app_cunsole.invoices.serializers import CustomerinvsummarySerializer
from app_cunsole.users.models import Account
from app_cunsole.users.serializers import AccountSerializer
from app_cunsole.users.serializers import UserSerializer

from .serializers import InvoiceSerializer


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
            if customer_id and not Customer.objects.filter(id=customer_id).exists():
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


@csrf_exempt
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


@csrf_exempt
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
            account_customers = customers.objects.filter(account_id=account.id)

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


@csrf_exempt
@api_view(["GET"])
@permission_classes([IsAuthenticated])
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


@csrf_exempt
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
            customers_list = customers.objects.filter(account_id=account.id)

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


@csrf_exempt
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
