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
    is_disabled = models.BooleanField(default=False)


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
    is_spf_verified = models.BooleanField(default=False)
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

    def generate_spf_record(self):
        """Generate SPF record based on the email provider's SMTP server."""
        if self.email_provider:
            return f"v=spf1 include:{self.email_provider.smtp_server} -all"
        return None

    def save(self, *args, **kwargs):
        if not self.spf_record:
            self.spf_record = self.generate_spf_record()
        super().save(*args, **kwargs)


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
    


# class Domainconfig(models.Model):
#     id = models.AutoField(primary_key=True)
#     name = models.CharField(max_length=255, unique=True)  # Domain name
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     account = models.ForeignKey(Account, on_delete=models.CASCADE)  # Links to the associated Account
#     mail_from_domain = models.CharField(max_length=255)  # Custom MAIL FROM domain
#     spf_record = models.TextField()  # SPF record for the domain
#     dmarc_record = models.TextField()  # DMARC record for the domain
#     verification_status = models.BooleanField(default=False)  # Verification status
#     created_at = models.DateTimeField(auto_now_add=True)  # When the domain was added
#     updated_at = models.DateTimeField(auto_now=True)  # When the domain was last updated
#     is_disabled = models.BooleanField(default=False)  # 0 for enabled, 1 for disabled

#     class Meta:
#         db_table = "Domainconfig"

#     def __str__(self):
#         return self.name



class Domainconfig(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=False)  # Domain name (unique within account only)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)  # Links to associated Account

    mail_from_domain = models.CharField(max_length=255)  # Custom MAIL FROM domain
    spf_record = models.TextField()  # SPF record for the domain
    dmarc_record = models.TextField()  # DMARC record for the domain

    mailing_address = models.EmailField(
        max_length=255, null=True, blank=True,
        help_text="Email address to send mail from for this domain"
    )

    is_default = models.BooleanField(
        default=False,
        help_text="Whether this domain is the default for the account"
    )  # Indicates if it's the default domain

    is_disabled = models.BooleanField(default=False)  # Whether the domain is disabled
    verification_status = models.BooleanField(default=False)  # Verification status

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "Domainconfig"
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'account'],
                condition=models.Q(is_disabled=False),
                name='unique_domain_per_account'
            )
        ]

    def __str__(self):
        return self.name



class DNSRecord(models.Model):
    RECORD_TYPES = (
        ('CNAME', 'CNAME'),
        ('MX', 'MX'),
        ('TXT', 'TXT'),
        ('DKIM', 'DKIM'),  # Adding DKIM as a record type
    )
    id = models.AutoField(primary_key=True)
    domainconfig = models.ForeignKey(Domainconfig, on_delete=models.CASCADE)  # Link to the Domain
    record_type = models.CharField(max_length=5, choices=RECORD_TYPES)  # Type of DNS record
    name = models.CharField(max_length=255)  # The name of the DNS record
    value = models.TextField()  # The value of the DNS record
    selector = models.CharField(max_length=255, null=True, blank=True)  # DKIM selector (optional)
    created_at = models.DateTimeField(auto_now_add=True)  # When the record was created
    updated_at = models.DateTimeField(auto_now=True)  # When the record was last updated
    is_disabled = models.BooleanField(default=False)

    class Meta:
        db_table = "DNSRecord"

    def __str__(self):
        return self.name


