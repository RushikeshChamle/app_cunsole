from django.conf import settings

import uuid
from django.db import models



import uuid
from django.db import models



class Account(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    created_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    email = models.EmailField(max_length=255, unique=True, null=True, blank=True)  # Account contact email
    phone_number = models.CharField(max_length=15, null=True, blank=True)  # Optional phone number
    address = models.TextField(null=True, blank=True)  # Address for the account
    industry = models.CharField(max_length=100, null=True, blank=True)  # Type of industry (optional)
    credit_limit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Credit limit for account
    updated_date = models.DateTimeField(auto_now=True)  # Automatically update timestamp on modification
    is_active = models.BooleanField(default=True)  # Status of account
    # Flags for email
    is_email_whitelabeled = models.BooleanField(default=False)  # Flag for email white-labeling
    is_verified = models.BooleanField(default=False)  # Flag for email verification

    class Meta:
        db_table = "account"
    





class Customers(models.Model):
    # Basic Details
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    externalid = models.CharField(max_length=255, blank=True, null=True)  # For syncing with external systems
    name = models.CharField(max_length=255)
    companyname = models.CharField(max_length=255, blank=True, null=True)
    industrytype = models.CharField(max_length=100, blank=True, null=True)

    # Contact Information
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    website = models.URLField(max_length=255, blank=True, null=True)  # New Field

    # Address Information
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    postalcode = models.CharField(max_length=20, blank=True, null=True)

    # Financial Information
    taxid = models.CharField(max_length=50, blank=True, null=True)
    currency = models.CharField(max_length=10, default='USD')  # New Field
    paymentterms = models.CharField(max_length=100, blank=True, null=True)  # e.g., "Net 30", "Net 45"
    creditlimit = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    discount = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)  # New Field
    account_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)  # New Field


# Categorization
    customer_category = models.CharField(
        max_length=50, 
        choices=[('regular', 'Regular'), ('premium', 'Premium'), ('delinquent', 'Delinquent')],
        blank=True, null=True  # New Field
    )
    risk_level = models.CharField(
        max_length=50, 
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')],
        blank=True, null=True  # New Field
    )

    # Integrations & Identification
    erp_system = models.CharField(max_length=100, blank=True, null=True)  # New Field for ERP Integration
    crm_id = models.CharField(max_length=255, blank=True, null=True)  # Sync with CRM System
    referral_source = models.CharField(max_length=100, blank=True, null=True)  # Track referrals (New Field)



    # Notes and Status
    notes = models.TextField(blank=True, null=True)
    isactive = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Relationships
    account = models.ForeignKey("Account", on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = "customers"

    def __str__(self):
        return self.name




class Customer_contact(models.Model):
    ROLE_CHOICES = [
        ("finance_manager", "Finance Manager"),
        ("ar_specialist", "Accounts Receivable Specialist"),
        ("ceo", "CEO"),
        ("cfo", "CFO"),
        ("accountant", "Accountant"),
        ("billing_manager", "Billing Manager"),
        ("collections_agent", "Collections Agent"),
        ("ap_specialist", "Accounts Payable Specialist"),
        ("customer_service", "Customer Service Representative"),
        ("sales_rep", "Sales Representative"),
        ("legal", "Legal Counsel"),
        ("other", "Other"),
    ]

    id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customers, related_name="contacts", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True, null=True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    notes = models.TextField(blank=True, null=True)
    is_disabled = models.BooleanField(default=False)

    class Meta:
        db_table = "cust_contacts"

    def __str__(self):
        return f"{self.name} ({self.get_role_display()})"






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





# Communication Templates
class CommunicationTemplate(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    type = models.CharField(max_length=50, choices=[
        ('invoice', 'Invoice'),
        ('reminder', 'Reminder'),
        ('late_payment', 'Late Payment'),
        ('thank_you', 'Thank You'),
        ('custom', 'Custom')
    ])
    account = models.ForeignKey('customer.Account', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "communication_templates"



# Communication Log
class CommunicationLog(models.Model):
    id = models.AutoField(primary_key=True)
    customer = models.ForeignKey('customer.Customers', on_delete=models.CASCADE)
    invoice = models.ForeignKey('invoices.Invoices', on_delete=models.CASCADE, null=True, blank=True)
    template = models.ForeignKey(CommunicationTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    sent_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=[
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('opened', 'Opened'),
        ('clicked', 'Clicked'),
        ('bounced', 'Bounced')
    ])
    channel = models.CharField(max_length=20, choices=[
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('letter', 'Letter')
    ])

    class Meta:
        db_table = "communication_log"



# Workflow
class Workflow(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    account = models.ForeignKey('customer.Account', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "workflows"


# Workflow Step
class WorkflowStep(models.Model):
    id = models.AutoField(primary_key=True)
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='steps')
    order = models.PositiveIntegerField()
    action_type = models.CharField(max_length=50, choices=[
        ('send_email', 'Send Email'),
        ('send_sms', 'Send SMS'),
        ('create_task', 'Create Task'),
        ('update_invoice', 'Update Invoice')
    ])
    template = models.ForeignKey(CommunicationTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    delay_days = models.PositiveIntegerField(default=0)
    condition = models.TextField(blank=True, null=True)  # JSON field for conditions

    class Meta:
        db_table = "workflow_steps"
        ordering = ['order']

# Task
class Task(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    due_date = models.DateTimeField()
    assigned_to = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='assigned_tasks')
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='created_tasks')
    customer = models.ForeignKey('customer.Customers', on_delete=models.CASCADE, null=True, blank=True)
    invoice = models.ForeignKey('invoices.Invoices', on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tasks"



# Dispute
class Dispute(models.Model):
    id = models.AutoField(primary_key=True)
    invoice = models.ForeignKey('invoices.Invoices', on_delete=models.CASCADE)
    customer = models.ForeignKey('customer.Customers', on_delete=models.CASCADE)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=[
        ('open', 'Open'),
        ('under_review', 'Under Review'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed')
    ])
    opened_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='opened_disputes')
    assigned_to = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='assigned_disputes')
    resolution = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "disputes"







class ActivityLog(models.Model):
    ACTIVITY_TYPES = (
        (0, 'Invoice Created'),
        (1, 'Invoice Updated'),
        (2, 'Invoice Status Changed'),
        (3, 'Payment Created'),
        (4, 'Payment Updated'),
        (5, 'Email Trigger Created'),
        (6, 'Email Trigger Updated'),
        (7, 'Email Sent'),
        (8, 'Other'),
    )

    EMAIL_STATUS_CHOICES = (
        (0, 'Sent'),
        (1, 'Failed'),
        (2, 'Pending'),
    )

    account = models.ForeignKey('customer.Account', on_delete=models.CASCADE, related_name='activity_logs')
    user = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)
    activity_type = models.IntegerField(choices=ACTIVITY_TYPES)
    invoice = models.ForeignKey('invoices.Invoices', on_delete=models.CASCADE, null=True, blank=True)
    payment = models.ForeignKey('invoices.Payment', on_delete=models.CASCADE, null=True, blank=True)
    email_trigger = models.ForeignKey(EmailTrigger, on_delete=models.CASCADE, null=True, blank=True)
    email_subject = models.CharField(max_length=255, null=True, blank=True)
    email_description = models.CharField(max_length=255, null=True, blank=True)
    email_from = models.EmailField(null=True, blank=True)
    email_to = models.TextField(null=True, blank=True)
    email_cc = models.TextField(null=True, blank=True)
    email_bcc = models.TextField(null=True, blank=True)
    email_status = models.IntegerField(choices=EMAIL_STATUS_CHOICES, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_disabled = models.BooleanField(default=False)

    class Meta:
        db_table = 'activity_logs'

    def __str__(self):
        return f"{self.get_activity_type_display()} on {self.created_at}"




class AIInteraction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    account = models.ForeignKey("Account", on_delete=models.CASCADE)
    query = models.TextField()
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ai_interactions'
        ordering = ['-created_at']