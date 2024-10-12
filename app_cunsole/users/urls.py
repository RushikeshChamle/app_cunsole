from django.urls import path

from .views import CustomTokenObtainPairView

# from .views import TokenRefreshView
from .views import create_account
from .views import create_user
from .views import signup
from .views import user_detail_view
from .views import user_redirect_view
from .views import user_update_view, get_accounts_and_users, email_provider_list, email_provider_detail
from .views import user_update_view, email_configuration_list, email_configuration_detail, email_verification_log_list, email_verification_log_detail
from . import views
from .views import generate_dkim_keys
from .views import add_domain, check_verification_status, get_dns_records


app_name = "users"


urlpatterns = [
    path("~redirect/", view=user_redirect_view, name="redirect"),
    path("~update/", view=user_update_view, name="update"),
    path("<int:pk>/", view=user_detail_view, name="detail"),
    path("signup/", signup, name="signup"),
    path("create_user/", create_user, name="create_user"),
    path("create_account/", create_account, name="create_account"),
    path("signin/", CustomTokenObtainPairView.as_view(), name="signin"),
    path('accounts_users/', get_accounts_and_users, name='accounts_users'),

    # # Email Providers
    # path('providers/', email_provider_list, name='email-provider-list'),   # List all providers or create a new one
    # path('providers/<int:pk>/', email_provider_detail, name='email-provider-detail'),  # Retrieve, update, or delete a specific provider

    # # Email Configurations
    # path('configurations/', email_configuration_list, name='email-configuration-list'),  # List all configurations or create a new one
    # path('configurations/<int:pk>/', email_configuration_detail, name='email-configuration-detail'),  # Retrieve, update, or delete a specific configuration

    # # Email Verification Logs
    # path('verification-logs/', email_verification_log_list, name='email-verification-log-list'),  # List all verification logs or create a new log
    # path('verification-logs/<int:pk>/', email_verification_log_detail, name='email-verification-log-detail'),  # Retrieve, update, or delete a specific log
    # path('configurations/<int:pk>/generate-dkim/', generate_dkim_record, name='generate-dkim'),


     # EmailProvider URLs
    path('providers/', views.email_provider_list, name='email-provider-list'),
    path('providers/<int:pk>/', views.email_provider_detail, name='email-provider-detail'),

    # EmailConfiguration URLs
    path('configurations/', views.email_configuration_list, name='email-configuration-list'),
    path('configurations/<int:pk>/', views.email_configuration_detail, name='email-configuration-detail'),
    path('configurations/<int:pk>/generate-keys/', views.generate_dkim_keys_view, name='generate-dkim-keys'),
    path('configurations/<int:pk>/verify-records/', views.verify_dns_records_view, name='verify-dns-records'),

    # EmailVerificationLog URLs
    path('verification-logs/', views.email_verification_log_list, name='email-verification-log-list'),
    path('verification-logs/<int:pk>/', views.email_verification_log_detail, name='email-verification-log-detail'),

    # GlobalEmailSettings URL
    path('global-settings/', views.global_email_settings, name='global-email-settings'),

    path('email-configurations/<int:pk>/update-spf/', views.update_spf_record, name='update-spf-record'),


    path('configurations/<int:pk>/dmarc/', views.update_dmarc_settings, name='update-dmarc-settings'),
    path('configurations/<int:pk>/stats/', views.get_sending_stats, name='get-sending-stats'),
    path('configurations/<int:pk>/send/', views.send_email, name='send-email'),
    path('configurations/<int:pk>/verify-and-test/', views.verify_and_test_email, name='verify-and-test-email'),

    path('domains/add/', add_domain, name='add_domain'),
    path('domains/status/<int:domain_id>/', check_verification_status, name='check_verification_status'),
    path('domains/records/<int:domain_id>/', get_dns_records, name='get_dns_records'),





]

    # path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

