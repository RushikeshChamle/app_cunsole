from rest_framework import serializers

from app_cunsole.customer.models import Customers , EmailTrigger

from .models import Invoices, Payment


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoices
        fields = "__all__"  # Include all fields or specify the ones you need
        extra_kwargs = {
            "account": {"required": False},
            "customerid": {"required": False},
        }


class InvoicedataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoices
        fields = "__all__"


class CustomerinvsummarySerializer(serializers.ModelSerializer):
    total_amount_to_pay = serializers.SerializerMethodField()
    total_paid_amount = serializers.SerializerMethodField()

    class Meta:
        model = Customers
        fields = [
            "id",
            "name",
            "email",
            "phone",
            "total_amount_to_pay",
            "total_paid_amount",
        ]


    def get_total_amount_to_pay(self, obj):
        # Use a different variable name to avoid conflict
        customer_invoices = Invoices.objects.filter(customerid=obj.id)
        return sum(invoice.total_amount for invoice in customer_invoices)

    def get_total_paid_amount(self, obj):
        # Use a different variable name to avoid conflict
        customer_invoices = Invoices.objects.filter(customerid=obj.id)
        return sum(invoice.paid_amount for invoice in customer_invoices)

    def get_invoices(self, obj):
        customer_invoices = Invoices.objects.filter(customerid=obj.id)
        return InvoiceSerializer(customer_invoices, many=True).data


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"



class EmailTriggerDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailTrigger
        fields = '__all__'

class InvoiceWithTriggersSerializer(serializers.ModelSerializer):
    email_triggers = serializers.SerializerMethodField()

    class Meta:
        model = Invoices
        fields = '__all__'

    def get_email_triggers(self, obj):
        triggers = EmailTrigger.objects.filter(account=obj.account, isactive=True)
        return EmailTriggerDetailSerializer(triggers, many=True).data
    

from .models import Invoices
from django.db.models import Sum
from django.utils import timezone


class CustomerDueSerializer(serializers.ModelSerializer):
    due_amount = serializers.SerializerMethodField()
    due_in_days = serializers.SerializerMethodField()

    class Meta:
        model = Customers
        fields = ['name', 'due_amount', 'due_in_days']

    def get_due_amount(self, obj):
        # Sum of all unpaid amounts in invoices for this customer
        total_due = Invoices.objects.filter(customerid=obj.id, status=0).aggregate(due_sum=Sum('total_amount'))['due_sum'] or 0
        return total_due

    def get_due_in_days(self, obj):
        # Get the shortest due date for unpaid invoices
        nearest_due_date = Invoices.objects.filter(customerid=obj.id, status=0).order_by('duedate').first()
        if nearest_due_date:
            delta = nearest_due_date.duedate - timezone.now()
            return delta.days
        return None