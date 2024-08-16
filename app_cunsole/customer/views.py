import json

import jwt
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from app_cunsole.customer.models import Customers
from app_cunsole.users.models import User

from .serializers import CustomerSerializer






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
