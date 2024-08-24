import uuid

from django.db import models

from app_cunsole.customer.models import Account


class Invoices(models.Model):
    STATUS_CHOICES = [
        (0, 'Due'),
        (1, 'Partial'),
        (2, 'Completed'),
        (3, 'Writeoff'),
    ]
    customid = models.CharField(max_length=255, null=True)
    externalid = models.CharField(max_length=255, blank=True, null=True)
    issuedat = models.DateTimeField(null=True)
    duedate = models.DateTimeField(null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    currency = models.CharField(max_length=3, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    customerid = models.UUIDField()  # Change this to UUIDField to match your database
    status = models.IntegerField(choices=STATUS_CHOICES, null=True, blank=True)  # New field
    # dunningplanid = models.ForeignKey(DunningPlan, on_delete=models.SET_NULL, null=True, blank=True)
    # dunningplanid = models.UUIDField()  # Change this to UUIDField to match your database
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "invoices"

    def __str__(self):
        return f"invoices {self.customid} for {self.customers.name}"


class Payment(models.Model):
    invoice = models.ForeignKey(Invoices, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    method = models.CharField(max_length=50, blank=True, null=True)  # e.g., 'Credit Card', 'Bank Transfer'
    reference = models.CharField(max_length=255, blank=True, null=True)  # e.g., transaction ID or check number
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True)  # New field
    # user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)  # New field
    user = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True )
    class Meta:
        db_table = "payments"

    def __str__(self):
        return f"Payment of {self.amount} for invoice {self.invoice.customid}"



class Plan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    billing_cycle = models.CharField(max_length=50, blank=True, null=True)
    features = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "plans"

    def __str__(self):
        return self.name


class PromiseToPay(models.Model):
    invoice = models.ForeignKey(Invoices, on_delete=models.CASCADE)
    date = models.DateField()
    comment = models.TextField(blank=True, null=True)
    pausedunning = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "promise_to_pay"

    def __str__(self):
        return f"Promise to Pay for Invoice {self.invoice.customid}"


class DunningPlan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "dunning_plan"

    def __str__(self):
        return self.name
