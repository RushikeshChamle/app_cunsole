import datetime
import json
from django.middleware.csrf import get_token
from django.utils import timezone
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
from .serializers import UserdataSerializer, UserSerializer
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import EmailProvider, EmailConfiguration, EmailVerificationLog
from .serializers import EmailProviderSerializer, EmailConfigurationSerializer, EmailVerificationLogSerializer
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import EmailProvider, EmailConfiguration, EmailVerificationLog, GlobalEmailSettings
from .serializers import EmailProviderSerializer, EmailConfigurationSerializer, EmailVerificationLogSerializer, GlobalEmailSettingsSerializer
from .utils import verify_dns_records, generate_dkim_keys
from .utils import verify_dns_records, verify_dmarc_record, send_test_email
from .models import EmailConfiguration
from .utils import verify_spf_record

from .models import User

from typing import Optional
from django.db.models import QuerySet
from django.contrib.auth import get_user_model

from typing import Optional
from django.db.models import QuerySet
from django.contrib.auth.models import User


User = get_user_model()



SECRET_KEY = "django-insecure-3t!a&dtryebf_9n(zhm&b#%(!nqc67hisav6hy02faz_ztb=_$"  # Replace with your actual secret key


from django.contrib.auth import get_user_model

User = get_user_model()

class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    slug_field = "id"
    slug_url_kwarg = "id"


user_detail_view = UserDetailView.as_view()


from typing import TYPE_CHECKING, Optional
from django.db.models import QuerySet

if TYPE_CHECKING:
    from .models import User  # Import only for type checking

from .models import User


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


# previous with the pages routing which cause errors
# class CustomTokenObtainPairView(TokenObtainPairView):
#     serializer_class = CustomTokenObtainPairSerializer

#     def post(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         try:
#             serializer.is_valid(raise_exception=True)
#         except serializers.ValidationError as e:
#             return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

#         response = Response(serializer.validated_data, status=status.HTTP_200_OK)
#         response.set_cookie(
#             key=settings.SIMPLE_JWT["AUTH_COOKIE"],
#             value=serializer.validated_data["access"],
#             expires=settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"],
#             secure=settings.SIMPLE_JWT.get("AUTH_COOKIE_SECURE", False),
#         )
#         response.set_cookie(
#             key=settings.SIMPLE_JWT["REFRESH_COOKIE"],
#             value=serializer.validated_data["refresh"],
#             expires=settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"],
#             secure=settings.SIMPLE_JWT.get("AUTH_COOKIE_SECURE", False),
#         )
#         return response
    

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            return Response(e.detail)

        response = Response(serializer.validated_data)
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




@api_view(["GET"])
def get_accounts_and_users(request):
    """
    Retrieve all accounts and users linked to the authenticated user's account.

    This view requires that the user is authenticated. It fetches all accounts and users associated
    with the authenticated user's account. The data is serialized and returned in the response.

    Returns:
        Response: A JSON response containing the accounts and users data and a status code.
                  If authentication is not provided, returns a 401 Unauthorized error.
    """

    try:
        if request.user_is_authenticated:
            user = request.user_id
            account = request.user_account  # Assuming each user is linked to an account

            if not account:
                return Response(
                    {"error": "User does not have an associated account."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Fetch accounts and users based on the authenticated user's account
            accounts = Account.objects.filter(id=account.id)
            users = User.objects.filter(account=account)

            # Serialize the data
            account_serializer = AccountSerializer(accounts, many=True)
            user_serializer = UserSerializer(users, many=True)

            # Return the response
            return Response({
                "accounts": account_serializer.data,
                "users": user_serializer.data
            }, status=status.HTTP_200_OK)

        return Response(
            {"error": "Authentication credentials were not provided."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





# EmailProvider views
@api_view(['GET', 'POST'])
def email_provider_list(request):
    """
    List all email providers or create a new one.

    Handles listing and creating email providers.
    
    GET:
    - Fetches and returns a list of all email providers.
    
    POST:
    - Validates and creates a new email provider.
    - On success, returns the new provider with status 201.
    - On failure, returns validation errors with status 400.
    """
    if request.method == 'GET':
        providers = EmailProvider.objects.all()
        serializer = EmailProviderSerializer(providers, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = EmailProviderSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    




@api_view(['GET', 'PUT', 'DELETE'])
def email_provider_detail(request, pk):
    """


    

    """
    provider = get_object_or_404(EmailProvider, pk=pk)

    if request.method == 'GET':
        serializer = EmailProviderSerializer(provider)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = EmailProviderSerializer(provider, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        provider.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)






# EmailConfiguration views
@api_view(['GET', 'POST'])
def email_configuration_list(request):
    """
    List all email configurations or create a new one.
    """
    if request.method == 'GET':
        configurations = EmailConfiguration.objects.all()
        serializer = EmailConfigurationSerializer(configurations, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = EmailConfigurationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    



@api_view(['GET', 'PUT', 'DELETE'])
def email_configuration_detail(request, pk):
    """
    Handles retrieving, updating, or deleting a specific email configuration.
    
    GET:
    - Retrieves and returns the email configuration with the given `pk`.
    
    PUT:
    - Updates the email configuration with the provided data.
    - On success, returns the updated configuration.
    - On failure, returns validation errors with status 400.
    
    DELETE:
    - Deletes the email configuration and returns status 204 (No Content).
    """
    configuration = get_object_or_404(EmailConfiguration, pk=pk)

    if request.method == 'GET':
        serializer = EmailConfigurationSerializer(configuration)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = EmailConfigurationSerializer(configuration, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        configuration.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    


@api_view(['POST'])
def generate_dkim_keys_view(request, pk):
    """
    Generate DKIM keys for a specific email configuration.

    Generate and assign DKIM keys for a specific email configuration.

    POST:
    - Generates DKIM private and public keys.
    - Assigns the keys to the email configuration with the given `pk`.
    - Saves the updated configuration and returns a success message.

    """
    configuration = get_object_or_404(EmailConfiguration, pk=pk)
    private_key, public_key = generate_dkim_keys()
    configuration.dkim_private_key = private_key
    configuration.dkim_public_key = public_key
    configuration.save()
    return Response({'message': 'DKIM keys generated successfully'})



@api_view(['POST'])
def verify_dns_records_view(request, pk):
    """

    Verify DNS records for a specific email configuration.
    
    POST:
    - Verifies the DNS records of the email configuration identified by `pk`.
    - Returns the verification results.
    """

    # Fetch the email configuration by primary key (pk) or return 404 if not found
    configuration = get_object_or_404(EmailConfiguration, pk=pk)

    # Verify DNS records for the configuration
    verification_results = verify_dns_records(configuration)

    # Return the verification results
    return Response(verification_results)

# EmailVerificationLog views

@api_view(['GET', 'POST'])
def email_verification_log_list(request):
    """
    List all email verification logs or create a new one.

    GET:
    - Retrieves and returns all email verification logs.
    
    POST:
    - Creates a new email verification log if the data is valid.
    - On success, returns the created log with status 201.
    - On failure, returns validation errors with status 400.

    """
    if request.method == 'GET':

        # Fetch all email verification logs
        logs = EmailVerificationLog.objects.all()


        # Serialize the logs data
        serializer = EmailVerificationLogSerializer(logs, many=True)

        # Return the serialized logs
        return Response(serializer.data)

    elif request.method == 'POST':
        # Serialize incoming data for a new email verification log
        serializer = EmailVerificationLogSerializer(data=request.data)
        
        
        # Check if the provided data is valid
        if serializer.is_valid():
            # Save the new log and return it
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        # Return errors if validation fails
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


@api_view(['GET'])
def email_verification_log_detail(request, pk):
    """
    Retrieve an email verification log.

    GET:
    - Retrieves and returns the email verification log identified by `pk`.

    """
    # Fetch the email verification log by primary key or return 404 if not found
    log = get_object_or_404(EmailVerificationLog, pk=pk)
    serializer = EmailVerificationLogSerializer(log)
    # Return the serialized log
    return Response(serializer.data)



# GlobalEmailSettings views
@api_view(['GET', 'PUT'])
def global_email_settings(request):
    """
    Retrieve or update global email settings.

    GET:
    - Retrieves and returns the global email settings.
    
    PUT:
    - Updates the global email settings with the provided data.
    - On success, returns the updated settings.
    - On failure, returns validation errors with status 400.

    """

    # Fetch or create a global email settings instance with a fixed pk of 1
    settings, created = GlobalEmailSettings.objects.get_or_create(pk=1)

    if request.method == 'GET':

        # Serialize and return the global email settings
        serializer = GlobalEmailSettingsSerializer(settings)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = GlobalEmailSettingsSerializer(settings, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    



from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import EmailConfiguration, SendingStats
from .utils import verify_dmarc_record, check_sending_limit, increment_sent_emails

@api_view(['POST'])
def update_dmarc_settings(request, pk):
    """
    Update the DMARC settings for a specific email configuration.

    POST:
    - Updates DMARC policy and percentage for the configuration identified by `pk`.
    - Regenerates the DMARC record and verifies it.
    - Returns the updated DMARC record and verification status.
    """

    
    try:
        # Fetch the email configuration by pk, return 404 if not found
        config = EmailConfiguration.objects.get(pk=pk)
    except EmailConfiguration.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    

    # Update the DMARC policy and percentage with provided values or keep current
    config.dmarc_policy = request.data.get('dmarc_policy', config.dmarc_policy)
    config.dmarc_pct = request.data.get('dmarc_pct', config.dmarc_pct)
    
    
    # Generate the DMARC record and save the updated configuration
    config.dmarc_record = config.generate_dmarc_record()
    config.save()


    # Return the updated DMARC record and verification status
    return Response({
        'dmarc_record': config.dmarc_record,
        'is_verified': verify_dmarc_record(config)
    })




@api_view(['GET'])
def get_sending_stats(request, pk):
    """
    Retrieve sending statistics for a specific email configuration.

    GET:
    - Retrieves the daily sending stats, including the daily limit, emails sent, and remaining quota.
    """

    try:
        # Fetch the email configuration by pk, return 404 if not found
        config = EmailConfiguration.objects.get(pk=pk)
    except EmailConfiguration.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    # Get today's date
    today = timezone.now().date()

    # Fetch or create sending stats for the specific email configuration and date
    stats, created = SendingStats.objects.get_or_create(
        email_configuration=config,
        date=today
    )
     # Return the daily limit, emails sent, and remaining quota

    return Response({
        'daily_limit': config.daily_send_limit,
        'emails_sent': stats.emails_sent,
        'remaining': max(0, config.daily_send_limit - stats.emails_sent)
    })



@api_view(['POST'])
def send_email(request, pk):
    try:
        config = EmailConfiguration.objects.get(pk=pk)
    except EmailConfiguration.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if not check_sending_limit(config):
        return Response({'error': 'Daily sending limit reached'}, status=status.HTTP_429_TOO_MANY_REQUESTS)

    # Here you would implement your actual email sending logic
    # For this example, we'll just increment the counter
    increment_sent_emails(config)

    return Response({'message': 'Email sent successfully'})




@api_view(['POST'])
def update_spf_record(request, pk):
    try:
        config = EmailConfiguration.objects.get(pk=pk)
    except EmailConfiguration.DoesNotExist:
        return Response({'error': 'Email configuration not found'}, status=status.HTTP_404_NOT_FOUND)

    config.spf_record = config.generate_spf_record()
    config.save()

    verification_result = verify_spf_record(config)
    
    return Response({
        'spf_record': config.spf_record,
        'is_verified': verification_result == 'Valid',
        'verification_result': verification_result
    })




@api_view(['POST'])
def verify_and_test_email(request, pk):

    """
    Verify DNS records and send a test email for a specific configuration.

    POST:
    - Verifies DNS and DMARC records for the email configuration identified by `pk`.
    - If all DNS records and DMARC pass, sends a test email.
    - On success, returns verification results and test email status.
    - On failure, returns error details or verification failures.
    
    
    """

    try:
        config = EmailConfiguration.objects.get(pk=pk)
    except EmailConfiguration.DoesNotExist:
        return Response({'error': 'Configuration not found'}, status=status.HTTP_404_NOT_FOUND)

    # Verify DNS records
    dns_results = verify_dns_records(config)
    dmarc_verified = verify_dmarc_record(config)

    all_verified = all(result == 'Valid' for result in dns_results.values()) and dmarc_verified

    if all_verified:
        # Send test email
        email_sent, message = send_test_email(config)
        if email_sent:
            config.is_verified = True
            config.save()
            return Response({
                'message': 'All DNS records verified and test email sent successfully',
                'dns_results': dns_results,
                'dmarc_verified': dmarc_verified,
                'email_sent': True
            })


        else:
            return Response({
                'message': 'DNS records verified, but test email failed',
                'dns_results': dns_results,
                'dmarc_verified': dmarc_verified,
                'email_error': message
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response({
            'message': 'DNS verification failed',
            'dns_results': dns_results,
            'dmarc_verified': dmarc_verified
        }, status=status.HTTP_400_BAD_REQUEST)
    





from .models import Domainconfig, DNSRecord
from .utils import add_domain_to_ses, get_verification_status, generate_dns_records



import logging
from django.contrib.auth.models import User
from .models import Account, Domainconfig, DNSRecord
from .utils import add_domain_to_ses, generate_dns_records
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status


from django.contrib.auth import get_user_model

User = get_user_model()

logger = logging.getLogger(__name__)



@api_view(["POST"])
def add_domain(request):
    """
    Add a new domain to the user's account.

    This view requires that the user is authenticated. It uses the data from the request to create a new
    domain record linked to the authenticated user's account. The function handles the domain addition to SES,
    creates the Domainconfig, and generates DNS records.

    The mailing_address, if provided, must use the same domain as the one being added.

    Returns:
        Response: A JSON response indicating the result of the domain addition attempt.
                  If authentication is not provided, returns a 401 Unauthorized error.
                  If the user doesn't have an associated account, returns a 400 Bad Request error.
                  If the mailing_address domain doesn't match the added domain, returns a 400 Bad Request error.
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

            domain = request.data.get('domain')
            mailing_address = request.data.get('mailing_address')
            is_default = request.data.get('is_default', False)

            if not domain:
                logger.warning("Domain is required but not provided.")
                return Response({'error': 'Domain is required'}, status=status.HTTP_400_BAD_REQUEST)

            # Validate mailing_address domain
            if mailing_address:
                mailing_domain = mailing_address.split('@')[-1]
                if mailing_domain.lower() != domain.lower():
                    logger.warning(f"Mailing address domain ({mailing_domain}) does not match the added domain ({domain}).")
                    return Response(
                        {'error': 'Mailing address must use the same domain as the one being added'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Add domain to SES
            ses_result = add_domain_to_ses(domain)
            if not ses_result:
                logger.error(f"Failed to add domain to SES for {domain}. SES result: {ses_result}")
                return Response({'error': 'Failed to add domain to SES'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Prepare data for Domainconfig creation
            domainconfig_data = {
                'name': domain,
                'user': user,
                'account': account.id,
                'mail_from_domain': ses_result['mail_from_domain'],
                'spf_record': "v=spf1 include:amazonses.com ~all",
                'dmarc_record': "v=DMARC1; p=none;",
                'mailing_address': mailing_address,
                'is_default': is_default,
                'verification_status': False  # Initially set to False
            }

            # Initialize serializer
            serializer = DomainconfigSerializer(data=domainconfig_data)

            # Validate and save
            if serializer.is_valid():
                domain_config = serializer.save()

                # Generate and save DNS records
                dns_records = generate_dns_records(domain, ses_result['dkim_tokens'], ses_result['mail_from_domain'])
                for record in dns_records:
                    DNSRecord.objects.create(
                        domainconfig=domain_config,
                        record_type=record['record_type'],
                        name=record['name'],
                        value=record['value'],
                        selector=record.get('selector')
                    )

                logger.info(f"Domain added successfully: {domain}")
                return Response(
                    {
                        "success": "Domain added successfully",
                        "domain_config": serializer.data,
                    },
                    status=status.HTTP_201_CREATED,
                )

            # Log validation errors
            logger.error(f"Validation errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"error": "Authentication required"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET'])
def check_verification_status(request, domain_id):
    try:
        domain_config = Domainconfig.objects.get(id=domain_id)
    except Domainconfig.DoesNotExist:
        return Response({'error': 'Domain configuration not found'}, status=status.HTTP_404_NOT_FOUND)

    verification_status = get_verification_status(domain_config.name)
    if verification_status == 'Success':
        domain_config.verification_status = True
        domain_config.save()
        return Response({'status': 'Verified'})
    elif verification_status == 'Pending':
        return Response({'status': 'Pending'})
    else:
        return Response({'status': 'Failed'}, status=status.HTTP_400_BAD_REQUEST)




@api_view(['GET'])
def get_dns_records(request, domain_id):
    try:
        domain_config = Domainconfig.objects.get(id=domain_id)
    except Domainconfig.DoesNotExist:
        return Response({'error': 'Domain configuration not found'}, status=status.HTTP_404_NOT_FOUND)

    dns_records = DNSRecord.objects.filter(domainconfig=domain_config)
    records_data = [
        {
            'record_type': record.record_type,
            'name': record.name,
            'value': record.value,
            'selector': record.selector
        } for record in dns_records
    ]

    return Response({
        'domain': domain_config.name,
        'dns_records': records_data
    })



from .models import Domainconfig
from .serializers import DomainconfigSerializer

@api_view(["GET"])
def get_account_domains(request):
    try:
        # Ensure the user is authenticated
        if request.user_is_authenticated:
            user = request.user_id
            account = request.user_account  # Assuming 'user_account' is set correctly

            if not account:
                return Response(
                    {"error": "User does not have an associated account"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Filter Domainconfig objects where account matches the user's account and is_disabled is False
            domains = Domainconfig.objects.filter(account=account, is_disabled=False)
            serializer = DomainconfigSerializer(domains, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(
            {"error": "Authentication credentials were not provided."},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    



# from rest_framework.decorators import api_view
# from rest_framework.response import Response
# from .utils import generate_email

# from rest_framework import status


# @api_view(['POST'])
# def generate_email_view(request):
#     try:
#         data = request.data
#         email_text = generate_email(
#             subject=data.get('subject'),
#             customer_name=data.get('customer_name'),
#             due_date=data.get('due_date'),
#             invoice_amount=data.get('invoice_amount')
#         )
#         return Response({"email_text": email_text}, status=status.HTTP_200_OK)
#     except Exception as e:
#         return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    





from rest_framework.decorators import api_view
from rest_framework.response import Response
from .utils import AzureOpenAIService

@api_view(['POST'])
def generate_text(request):
    try:
        # Print request data for debugging
        print("Received request data:", request.data)
        
        prompt = request.data.get('prompt')
        if not prompt:
            return Response({
                'status': 'error',
                'message': 'Prompt is required'
            }, status=400)

        ai_service = AzureOpenAIService()
        response = ai_service.generate_response(prompt)
        
        if response['status'] == 'error':
            return Response(response, status=500)
            
        return Response(response)

    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=500)





from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .utils import EmailGenerator
from django.core.exceptions import ValidationError
from decimal import Decimal
import datetime

@api_view(['POST'])
def generate_email_view(request):
    try:
        # Validate input data
        data = request.data
        required_fields = ['subject', 'customer_name', 'due_date', 'invoice_amount']
        
        # Check for missing fields
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return Response(
                {"error": f"Missing required fields: {', '.join(missing_fields)}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate date format
        try:
            # Assuming date format is YYYY-MM-DD
            due_date = datetime.datetime.strptime(data['due_date'], '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"error": "Invalid date format. Please use YYYY-MM-DD"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate invoice amount
        try:
            invoice_amount = Decimal(data['invoice_amount'])
            if invoice_amount <= 0:
                raise ValidationError("Invoice amount must be greater than 0")
        except (ValueError, ValidationError) as e:
            return Response(
                {"error": "Invalid invoice amount"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generate email
        email_generator = EmailGenerator()
        email_text = email_generator.generate_email(
            subject=data['subject'],
            customer_name=data['customer_name'],
            due_date=data['due_date'],
            invoice_amount=str(invoice_amount)
        )

        return Response({
            "status": "success",
            "email_text": email_text
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error in generate_email_view: {str(e)}", exc_info=True)
        return Response({
            "status": "error",
            "message": "An error occurred while generating the email",
            "detail": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    






    # testing email

from django.http import JsonResponse
from rest_framework.decorators import api_view
from .tasks import send_test_emails


@api_view(['POST'])
def trigger_email_test(request):
    """
    Trigger a test email to be sent.
    """
    email_data = {
        'subject': 'Test Email Subject',
        'message': 'This is a test email message.',
        'recipient_list': [request.data.get('email')]
    }

    # Call the Celery task to send the email
    task = send_test_emails.delay(email_data)

    return JsonResponse({
        'status': 'success',
        'task_id': task.id,
        'message': 'Email is being sent.'
    })


from django.http import JsonResponse
from celery.result import AsyncResult
import logging

# Set up logging
logger = logging.getLogger(__name__)

def check_email_status(request, task_id):
    try:
        task_result = AsyncResult(task_id)
        
        if task_result.state == 'PENDING':
            response = {
                'task_id': task_id,
                'status': task_result.state,
                'result': None,
            }
        elif task_result.state != 'FAILURE':
            response = {
                'task_id': task_id,
                'status': task_result.state,
                'result': task_result.result,
            }
        else:
            # Task failed
            response = {
                'task_id': task_id,
                'status': task_result.state,
                'result': str(task_result.info),  # Error message
            }
        
        return JsonResponse(response)
    
    except Exception as e:
        logger.error(f"Error checking email status for task {task_id}: {str(e)}")
        return JsonResponse({'error': 'An unexpected error occurred', 'details': str(e)}, status=500)
    




# without authentication
# @api_view(['POST'])
# def send_custom_email(request):
#     """
#     Send a custom email with user-defined content.
#     """
#     try:
#         # Extract email data from request
#         subject = request.data.get('subject')
#         message = request.data.get('message')
#         recipient_list = request.data.get('recipient_list')
#         cc_list = request.data.get('cc', [])  # Optional CC field

#         # Validate required fields
#         if not subject or not message or not recipient_list:
#             raise ValidationError("Subject, message, and recipient_list are required.")

#         # Prepare email data
#         email_data = {
#             'subject': subject,
#             'message': message,
#             'recipient_list': recipient_list,
#             'cc_list': cc_list,
#         }

#         # Trigger Celery task to send the email
#         task = send_test_emails.delay(email_data)

#         return Response({
#             'status': 'success',
#             'task_id': task.id,
#             'message': 'Your custom email is being sent.'
#         })

#     except ValidationError as e:
#         return Response({'status': 'error', 'message': str(e)}, status=400)





@api_view(['POST'])
def send_custom_email(request):
    """
    Send a custom email with user-defined content.
    """
    try:
    #     # Ensure the user is authenticated
        if request.user_is_authenticated:
            user = request.user_id
            account = request.user_account  # Assuming 'user_account' is set correctly

            if not account:
                return Response(
                    {"error": "User does not have an associated account"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(
                {"error": "User is not authenticated"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Extract email data from request
        subject = request.data.get('subject')
        message = request.data.get('message')
        recipient_list = request.data.get('recipient_list')
        cc_list = request.data.get('cc', [])  # Optional CC field

        # Validate required fields
        if not subject or not message or not recipient_list:
            raise ValidationError("Subject, message, and recipient_list are required.")

        # Prepare email data
        email_data = {
            'subject': subject,
            'message': message,
            'recipient_list': recipient_list,
            'cc_list': cc_list,
        }

        # Trigger Celery task to send the email
        task = send_test_emails.delay(email_data)

        return Response({
            'status': 'success',
            'task_id': task.id,
            'message': 'Your custom email is being sent.'
        })

    except ValidationError as e:
        return Response({'status': 'error', 'message': str(e)}, status=400)
