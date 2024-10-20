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
    issuedate = models.DateTimeField(null=True)
    duedate = models.DateTimeField(null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    currency = models.CharField(max_length=3, null=True)
    # total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    # paid_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    customerid = models.UUIDField()  # Change this to UUIDField to match your database
    status = models.IntegerField(choices=STATUS_CHOICES, null=True, blank=True ,default=0)  # New field
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    file_path = models.URLField(max_length=9000, blank=True, null=True)  # Shortened field name
    updated_at = models.DateTimeField(auto_now=True, null=True)
    reference = models.CharField( blank=True, null=True)  # e.g., transaction ID or check number
    currency_code = models.CharField(max_length=3, blank=True, null=True)
    # new advanced fields
    # Advanced fields
    is_discount_before_tax = models.BooleanField(null=True, blank=True, default=True)
    discount_type = models.CharField(max_length=50, blank=True, null=True)
    is_inclusive_tax = models.BooleanField(null=True, blank=True, default=False)
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=1)
    payment_terms = models.IntegerField(null=True, blank=True)
    payment_terms_label = models.CharField(max_length=50, blank=True, null=True)
    tax_authority_id = models.CharField(max_length=255, blank=True, null=True)
    avatax_use_code = models.CharField(max_length=50, blank=True, null=True)
    avatax_tax_code = models.CharField(max_length=50, blank=True, null=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0)

    # Aggregate tax amount at the invoice level
    total_tax_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # NEW


    account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    is_disabled = models.BooleanField(default=False)
    user = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True )

    class Meta:
        db_table = "invoices"

    def __str__(self):
        return f"invoices {self.customid} for {self.customers.name}"
    


class InvoiceDetails(models.Model):
    invoice = models.ForeignKey(Invoices, related_name='invoice_details', on_delete=models.CASCADE)
    item_id = models.CharField(max_length=255)
    project_id = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255)
    product_type = models.CharField(max_length=50)
    hsn_no = models.CharField(max_length=50, blank=True, null=True)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Calculated tax amount at the line-item level
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # NEW

    item_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "invoice_details"




class InvoiceCustomFields(models.Model):
    invoice = models.ForeignKey(Invoices, related_name='inv_custom_fields', on_delete=models.CASCADE)
    label = models.CharField(max_length=255)
    value = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = "inv_custom_fields"

class PaymentGateways(models.Model):
    invoice = models.ForeignKey(Invoices, related_name='payment_options', on_delete=models.CASCADE)
    gateway_name = models.CharField(max_length=50)
    configured = models.BooleanField(null=True, blank=True, default=False)
    additional_field1 = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = "payment_gateways"



class Payment(models.Model):
    invoice = models.ForeignKey(Invoices, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    method = models.CharField(max_length=50, blank=True, null=True)  # e.g., 'Credit Card', 'Bank Transfer'
    reference = models.CharField(max_length=255, blank=True, null=True)  # e.g., transaction ID or check number
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True)  # New field
    # user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)  # New field
    user = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True )
    is_disabled = models.BooleanField(default=False)
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
    is_disabled = models.BooleanField(default=False)

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
    is_disabled = models.BooleanField(default=False)

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
    is_disabled = models.BooleanField(default=False)

    class Meta:
        db_table = "dunning_plan"

    def __str__(self):
        return self.name
