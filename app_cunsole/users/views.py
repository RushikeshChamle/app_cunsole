import datetime
import json

import jwt
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import QuerySet
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView
from django.views.generic import RedirectView
from django.views.generic import UpdateView
from rest_framework import serializers
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from app_cunsole.customer.models import Account
from app_cunsole.users.models import User

from .models import User
from .serializers import AccountSerializer
from .serializers import CustomTokenObtainPairSerializer
from .serializers import UserCreationSerializer
from .serializers import UserdataSerializer

SECRET_KEY = "django-insecure-3t!a&dtryebf_9n(zhm&b#%(!nqc67hisav6hy02faz_ztb=_$"  # Replace with your actual secret key


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    slug_field = "id"
    slug_url_kwarg = "id"


user_detail_view = UserDetailView.as_view()


class UserUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    fields = ["name"]
    success_message = _("Information successfully updated")

    def get_success_url(self) -> str:
        assert self.request.user.is_authenticated  # type guard
        return self.request.user.get_absolute_url()

    def get_object(self, queryset: QuerySet | None = None) -> User:
        assert self.request.user.is_authenticated  # type guard
        return self.request.user


user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self) -> str:
        return reverse("users:detail", kwargs={"pk": self.request.user.pk})


user_redirect_view = UserRedirectView.as_view()


# @csrf_exempt
@api_view(["POST"])
def create_account(request):
    if request.method == "POST":
        serializer = AccountSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    return Response(
        {"error": "Method not allowed"},
        status=status.HTTP_405_METHOD_NOT_ALLOWED,
    )


# @csrf_exempt
@api_view(["POST"])
def signup(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_serializer = UserdataSerializer(data=data)
            if user_serializer.is_valid():
                # Save the user
                user = user_serializer.save()

                # Create a new account for the user
                account_data = {
                    "name": user.name,  # Adjust as per your account creation requirements
                    "is_active": True,  # Set default values or adjust based on requirements
                }
                account_serializer = AccountSerializer(data=account_data)
                if account_serializer.is_valid():
                    account = account_serializer.save()

                    # Associate the account with the user
                    # user.Account = account
                    user.account = account
                    user.save()

                    return Response(
                        {"message": "User successfully created"},
                        status=status.HTTP_201_CREATED,
                    )
                else:
                    # Delete the user if account creation fails to maintain consistency
                    user.delete()
                    return Response(
                        account_serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except json.JSONDecodeError:
            return Response(
                {"error": "Invalid JSON data"},
                status=status.HTTP_400_BAD_REQUEST,
            )
    else:
        return Response(
            {"error": "Method not allowed"},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )


# @csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def create_user(request):
    serializer = UserCreationSerializer(data=request.data)
    if serializer.is_valid():
        account_id = serializer.validated_data.get("account_id")
        try:
            account = Account.objects.get(id=account_id)
        except Account.DoesNotExist:
            return Response(
                {"error": "Account not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        user = User.objects.create_user(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
            name=serializer.validated_data.get("name", ""),
            contact=serializer.validated_data.get("contact", ""),
            account=account,
        )
        return Response(
            {"message": "User created successfully", "user_id": user.id},
            status=status.HTTP_201_CREATED,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# @csrf_exempt
@api_view(["POST"])
def signin(request):
    print("Signup API called")  # Debug print
    if request.method == "POST":
        email = request.data.get("email")
        password = request.data.get("password")
        user = User.objects.filter(email=email, password=password).first()

        if user:
            payload = {
                "user_id": user.id,
                "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24),
                "iat": datetime.datetime.utcnow(),
            }
            token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
            return Response({"message": "User login successful", "token": token})
        return Response(
            {"message": "Invalid credentials"},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    return Response(
        {"message": "Method not allowed"},
        status=status.HTTP_405_METHOD_NOT_ALLOWED,
    )



class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

        response = Response(serializer.validated_data, status=status.HTTP_200_OK)
        response.set_cookie(
            key=settings.SIMPLE_JWT["AUTH_COOKIE"],
            value=serializer.validated_data["access"],
            expires=settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"],
            secure=settings.SIMPLE_JWT.get("AUTH_COOKIE_SECURE", False),
        )
        response.set_cookie(
            key=settings.SIMPLE_JWT["REFRESH_COOKIE"],
            value=serializer.validated_data["refresh"],
            expires=settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"],
            secure=settings.SIMPLE_JWT.get("AUTH_COOKIE_SECURE", False),
        )
        return response
