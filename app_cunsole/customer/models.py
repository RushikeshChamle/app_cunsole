import uuid
from django.db import models
from django.db import models


class Account(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    created_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "account"


class Customers(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    externalid = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    postalcode = models.CharField(max_length=20, blank=True, null=True)
    taxid = models.CharField(max_length=50, blank=True, null=True)
    companyname = models.CharField(max_length=255, blank=True, null=True)
    industrytype = models.CharField(max_length=100, blank=True, null=True)
    paymentterms = models.CharField(max_length=100, blank=True, null=True)
    creditlimit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
    )
    notes = models.TextField(blank=True, null=True)
    isactive = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    user = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "customers"

    def __str__(self):
        return self.name



# New Model: EmailTrigger
class EmailTrigger(models.Model):
    CONDITION_CHOICES = [
        (0, 'Before Due Date'),
        (1, 'On Due Date'),
        (2, 'After Due Date'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    condition_type = models.IntegerField(choices=CONDITION_CHOICES, default=0)
    email_subject = models.CharField(max_length=255)
    email_body = models.TextField()
    days_offset = models.IntegerField(default=1)  # Number of days before/after due date
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    account = models.ForeignKey('customer.Account', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    isactive = models.BooleanField(default=True)

    class Meta:
        db_table = "email_trigger"

    def __str__(self):
        return self.name




# New Model: Rule
class Trigger_rule(models.Model):
    CONDITION_CHOICES = [
        (0, 'Before Due Date'),
        (1, 'On Due Date'),
        (2, 'After Due Date'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    condition_type = models.IntegerField(choices=CONDITION_CHOICES, default=0)
    days_offset = models.IntegerField(default=1)  # Number of days before/after due date
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    account = models.ForeignKey(Customers, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    isactive = models.BooleanField(default=True)

    class Meta:
        db_table = "trigger_rule"

    def __str__(self):
        return self.name



# # EmailLog model
# class EmailLog(models.Model):
#     recipient_email = models.EmailField()
#     subject = models.CharField(max_length=255)
#     body = models.TextField()
#     sent_at = models.DateTimeField(default=timezone.now)
#     invoice = models.ForeignKey('invoices.Invoices', on_delete=models.CASCADE, null=True, blank=True)
#     email_trigger = models.ForeignKey(EmailTrigger, on_delete=models.CASCADE, null=True, blank=True)
#     account = models.ForeignKey(Account, on_delete=models.CASCADE)
#     user = models.ForeignKey('users.User', on_delete=models.CASCADE)

#     class Meta:
#         db_table = "email_log"

#     def __str__(self):
#         return f"Email to {self.recipient_email} on {self.sent_at}"
