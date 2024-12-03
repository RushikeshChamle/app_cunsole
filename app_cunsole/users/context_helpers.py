from django.apps import apps

# Dynamically import models
Invoices = apps.get_model('invoices', 'Invoices')
Payment = apps.get_model('invoices', 'Payment')
Customers = apps.get_model('customer', 'Customers')
Account = apps.get_model('customer', 'Account')
CommunicationLog = apps.get_model('customer', 'CommunicationLog')
import datetime

import json


def serialize_datetime(obj):
    """
    Serialize datetime objects to ISO 8601 format.
    """
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()  # Convert to ISO 8601 string
    raise TypeError("Type not serializable")



# def extract_relevant_context(account):
#     return {
#         "account_details": {
#             "name": account.name,
#             "industry": account.industry,
#             "credit_limit": float(account.credit_limit),
#         },
#         "recent_invoices": get_recent_invoices(account),
#         "customer_info": get_customer_details(account),
#         "payment_history": get_payment_history(account),
#         "communication_logs": get_recent_communications(account),
#     }



# def extract_relevant_context(account):
#     return {
#         "account_details": {
#             "name": account.name,
#             "industry": account.industry,
#             "credit_limit": float(account.credit_limit),
#         },
#         "recent_invoices": get_recent_invoices(account),
#         "customer_info": get_customer_details(account),  # This will return a list now
#         "payment_history": get_payment_history(account),
#         "communication_logs": get_recent_communications(account),
#     }

def extract_relevant_context(account):
    context = {
        "account_details": {
            "name": account.name,
            "industry": account.industry,
            "credit_limit": float(account.credit_limit),
        },
        "recent_invoices": get_recent_invoices(account),
        "customer_info": get_customer_details(account),
        "payment_history": get_payment_history(account),
        "communication_logs": get_recent_communications(account),
    }
    
    # Serialize datetime fields in the context dictionary
    return json.loads(json.dumps(context, default=serialize_datetime))


# def get_recent_invoices(account, limit=5):
#     invoices = Invoices.objects.filter(account=account, is_disabled=False).order_by('-created_at')[:limit]
#     return [{"invoice_id": inv.customid, "total_amount": float(inv.total_amount)} for inv in invoices]


def get_recent_invoices(account, limit=5):
    invoices = Invoices.objects.filter(account=account, is_disabled=False).order_by('-created_at')[:limit]
    return [{"invoice_id": inv.customid, "total_amount": float(inv.total_amount), "created_at": inv.created_at.isoformat()} for inv in invoices]



# def get_customer_details(account):
#     try:
#         customer = Customers.objects.get(account=account)
#         return {"name": customer.name, "category": customer.customer_category}
#     except Customers.DoesNotExist:
#         return {}

def get_customer_details(account):
    customers = Customers.objects.filter(account=account)
    if customers.exists():
        customer_details = []
        for customer in customers:
            customer_details.append({
                "name": customer.name,
                "category": customer.customer_category
            })
        return customer_details
    else:
        return []


# def get_payment_history(account, limit=10):
#     payments = Payment.objects.filter(account=account, is_disabled=False).order_by('-payment_date')[:limit]
#     return [{"amount": float(p.amount), "date": p.payment_date} for p in payments]

def get_payment_history(account, limit=10):
    payments = Payment.objects.filter(account=account, is_disabled=False).order_by('-payment_date')[:limit]
    return [{"amount": float(p.amount), "date": p.payment_date.isoformat()} for p in payments]


# def get_recent_communications(account, limit=5):
#     logs = CommunicationLog.objects.filter(customer__account=account).order_by('-sent_at')[:limit]
#     return [{"subject": log.subject, "channel": log.channel} for log in logs]


def get_recent_communications(account, limit=5):
    logs = CommunicationLog.objects.filter(customer__account=account).order_by('-sent_at')[:limit]
    return [{"subject": log.subject, "channel": log.channel, "sent_at": log.sent_at.isoformat()} for log in logs]
