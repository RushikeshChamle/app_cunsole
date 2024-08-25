from rest_framework import serializers

from app_cunsole.customer.models import Customers

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
        fields = ['invoice', 'amount', 'method', 'reference', 'account', 'user']
