from typing import ClassVar

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import CharField
from django.db.models import EmailField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from app_cunsole.customer.models import Account
from .managers import UserManager
from django.core.validators import MinValueValidator, MaxValueValidator



class User(AbstractUser):
    """
    Default custom user model for app-cunsole.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """
    # First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]
    email = EmailField(_("email address"), unique=True)
    username = None  # type: ignore[assignment]
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    contact = models.CharField(max_length=15)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True)
    objects: ClassVar[UserManager] = UserManager()

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"pk": self.id})
    



# class EmailConfiguration(models.Model):
#     id = models.AutoField(primary_key=True)
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     domain_name = models.CharField(max_length=255, unique=True)
#     dkim_selector = models.CharField(max_length=50, blank=True, null=True)
#     dkim_public_key = models.TextField(blank=True, null=True)
#     dkim_private_key = models.TextField(blank=True, null=True)
#     spf_record = models.TextField(blank=True, null=True)
#     is_verified = models.BooleanField(default=False)
#     is_disabled = models.IntegerField(default=0)  # 0 for enabled, 1 for disabled
#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         db_table = "email_configuration"


# class EmailVerificationLog(models.Model):
#     id = models.AutoField(primary_key=True)
#     email_configuration = models.ForeignKey(EmailConfiguration, on_delete=models.CASCADE)
#     user = models.ForeignKey(User, on_delete=models.CASCADE)  # Links to the User who initiated the verification
#     account = models.ForeignKey(Account, on_delete=models.CASCADE)  # Links to the associated Account
#     verification_attempt_at = models.DateTimeField(auto_now_add=True)  # When verification was attempted
#     verification_status = models.CharField(max_length=50)  # Status: e.g., 'Success', 'Failure'
#     error_message = models.TextField(blank=True, null=True)  # Error details, if any
#     verification_type = models.CharField(max_length=10)  # DKIM/SPF (for logging different record types)

#     class Meta:
#         db_table = "email_verification_log"





# class EmailVerificationLog(models.Model):
#     STATUS_PENDING = 0
#     STATUS_SUCCESS = 1
#     STATUS_FAILURE = 2

#     id = models.AutoField(primary_key=True)
#     email_configuration = models.ForeignKey(EmailConfiguration, on_delete=models.CASCADE)
#     user = models.ForeignKey(User, on_delete=models.CASCADE)  # Links to the User who initiated the verification
#     account = models.ForeignKey(Account, on_delete=models.CASCADE)  # Links to the associated Account
#     verification_attempt_at = models.DateTimeField(auto_now_add=True)  # When verification was attempted
#     verification_status = models.IntegerField(default=STATUS_PENDING)  # Status as an integer flag
#     error_message = models.TextField(blank=True, null=True)  # Error details, if any
#     verification_type = models.CharField(max_length=10)  # DKIM/SPF (for logging different record types)

#     class Meta:
#         db_table = "email_verification_log"


# class GlobalEmailSettings(models.Model):
#     id = models.AutoField(primary_key=True)
#     default_sender_email = models.EmailField()
#     default_dkim_selector = models.CharField(max_length=50, blank=True, null=True)
#     smtp_server = models.CharField(max_length=255)
#     smtp_port = models.IntegerField()
#     smtp_username = models.CharField(max_length=255)
#     smtp_password = models.CharField(max_length=255)  # Could be stored encrypted
#     created_at = models.DateTimeField(auto_now_add=True)
    
#     class Meta:
#         db_table = "global_email_settings"



class EmailProvider(models.Model):
    """
    Represents different email service providers.
    """
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    smtp_server = models.CharField(max_length=255)
    smtp_port = models.PositiveIntegerField()
    use_tls = models.BooleanField(default=True)
    use_ssl = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        db_table = "email_provider"

    def __str__(self):
        return self.name


class EmailConfiguration(models.Model):
    """
    Configuration settings for a user's email domain.
    """
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)  # Links to the associated Account
    email_provider = models.ForeignKey(EmailProvider, on_delete=models.CASCADE, null=True)
    domain_name = models.CharField(max_length=255, unique=True)
    dkim_selector = models.CharField(max_length=50, blank=True, null=True)
    dkim_public_key = models.TextField(blank=True, null=True)
    dkim_private_key = models.TextField(blank=True, null=True)
    spf_record = models.TextField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    is_disabled = models.BooleanField(default=False)  # 0 for enabled, 1 for disabled
    created_at = models.DateTimeField(auto_now_add=True)
    dmarc_record = models.TextField(blank=True, null=True)
    dmarc_policy = models.CharField(
        max_length=10, 
        choices=[('none', 'None'), ('quarantine', 'Quarantine'), ('reject', 'Reject')],
        default='none'
    )
    dmarc_pct = models.IntegerField(
        default=100,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    daily_send_limit = models.PositiveIntegerField(default=10000)
    is_dmarc_verified = models.BooleanField(default=False)

    class Meta:
        db_table = "email_configuration"


    def generate_dkim_record(self):
        """Generate DKIM TXT record."""
        # Construct the DKIM TXT record based on existing fields
        if not self.dkim_selector or not self.dkim_public_key:
            raise ValueError("DKIM selector and public key must be set.")

        # Generate the DKIM record in the format:
        # selector._domainkey.yourdomain.com. IN TXT "v=DKIM1; k=rsa; p=yourpublickey"
        record = f"{self.dkim_selector}._domainkey.{self.domain_name} IN TXT \"v=DKIM1; k=rsa; p={self.dkim_public_key}\""
        return record
    

    def generate_dmarc_record(self):
        return f"v=DMARC1; p={self.dmarc_policy}; pct={self.dmarc_pct}; rua=mailto:dmarc@{self.domain_name}"



class SendingStats(models.Model):
    email_configuration = models.ForeignKey(EmailConfiguration, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    emails_sent = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('email_configuration', 'date')



class EmailVerificationLog(models.Model):
    """
    Logs the verification attempts for DKIM and SPF settings.
    """
    STATUS_PENDING = 0
    STATUS_SUCCESS = 1
    STATUS_FAILURE = 2

    id = models.AutoField(primary_key=True)
    email_configuration = models.ForeignKey(EmailConfiguration, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)  # Links to the associated Account
    verification_attempt_at = models.DateTimeField(auto_now_add=True)  # When verification was attempted
    verification_status = models.IntegerField(default=STATUS_PENDING)  # Status as an integer flag
    error_message = models.TextField(blank=True, null=True)  # Error details, if any
    verification_type = models.CharField(max_length=10)  # DKIM/SPF (for logging different record types)
    is_disabled = models.BooleanField(default=False)  #
    class Meta:
        db_table = "email_verification_log"



class GlobalEmailSettings(models.Model):
    """
    Global settings for email sending.
    """
    id = models.AutoField(primary_key=True)
    default_sender_email = models.EmailField()
    default_dkim_selector = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_disabled = models.BooleanField(default=False)  #

    class Meta:
        db_table = "global_email_settings"

    def __str__(self):
        return self.default_sender_email