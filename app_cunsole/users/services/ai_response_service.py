


import json
# from users.utils import AzureOpenAIService
from app_cunsole.users.utils import AzureOpenAIService

from app_cunsole.users.utils import AzureOpenAIService
from app_cunsole.users.context_helpers import extract_relevant_context

from decimal import Decimal

# from users.context_helpers import extract_relevant_context
# from customer.models import AIInteraction
from django.apps import apps
from celery import shared_task
from django.contrib.auth import get_user_model

# from customer.models import Account

User = apps.get_model('users', 'User')
# Dynamically import models
AIInteraction = apps.get_model('customer', 'AIInteraction')
Account = apps.get_model('customer', 'Account')
# User = get_user_model()
import logging

logger = logging.getLogger(__name__)






@shared_task
def generate_ai_response(account_id, user_query):
    """
    Asynchronously generate an AI response for a user's query and log the interaction.
    """
    try:
        # Use get_user_model() to fetch the user
        User = apps.get_model('users', 'User')
        
        # Use select_related to optimize the query
        user = User.objects.select_related('account').filter(account_id=account_id).first()

        if not user or not user.account:
            logger.error(f"User or account not found for account_id {account_id}")
            return None

        context = extract_relevant_context(user.account)
        prompt = f"""
        Context: {json.dumps(context)}
        User Query: {user_query}
        Provide a professional response leveraging the above context don't return respsoe in the email format only.
        Please also format it properly add proper pointer wherever it is necesaary so it is more redaable and make it action oriented
        break line whenre it is necessary so it is more redable
        """

        azure_openai_service = AzureOpenAIService()

        response = azure_openai_service.generate_response(prompt)
        if response['status'] == 'success':
            ai_response = response['data']
            log_ai_interaction(user, user.account, user_query, ai_response)
            return ai_response
        else:
            logger.error(f"AI response generation failed: {response['message']}")
            return f"Error: {response['message']}"

    except Exception as e:
        logger.error(f"Error generating AI response: {str(e)}")
        return f"An unexpected error occurred: {str(e)}"
    


def log_ai_interaction(user, account, query, response):
    """
    Log the AI interaction to the database for tracking purposes.
    """
    AIInteraction.objects.create(user=user, account=account, query=query, response=response)





# credit score services



import datetime
from django.apps import apps
import numpy as np
from django.db.models import Sum, Count
import datetime
from decimal import Decimal
import numpy as np
from django.apps import apps
from django.db.models import Sum, Count






import datetime
from decimal import Decimal
import numpy as np
from django.apps import apps
from django.db.models import Sum, Count
from django.core.exceptions import ObjectDoesNotExist


def calculate_customer_credit_score(customer):
    try:
        # Dynamically import models to avoid circular imports
        Payment = apps.get_model('invoices', 'Payment')
        Invoices = apps.get_model('invoices', 'Invoices')

        # Base credit score calculation logic
        try:
            payments = Payment.objects.filter(
                invoice__customerid=customer.id,
                is_disabled=False
            ).order_by('-payment_date')
        except Exception as e:
            payments = Payment.objects.none()
            print(f"Error fetching payments: {e}")

        try:
            invoices = Invoices.objects.filter(
                customerid=customer.id,
                is_disabled=False
            ).order_by('-created_at')
        except Exception as e:
            invoices = Invoices.objects.none()
            print(f"Error fetching invoices: {e}")

        # Initialize scoring components and financial metrics
        scoring_components = {
            'payment_timeliness': Decimal('0'),
            'payment_consistency': Decimal('0'),
            'invoice_volume': Decimal('0'),
            'credit_utilization': Decimal('0')
        }

        # Payment Metrics
        total_invoices = invoices.count()
        on_time_payments = 0
        late_payments = 0
        
        # Financial Calculations
        total_invoice_amount = Decimal('0')
        total_paid_amount = Decimal('0')
        total_outstanding_amount = Decimal('0')
        total_overdue_amount = Decimal('0')
        
        # Detailed Payment Analysis
        for invoice in invoices:
            # Safely convert to Decimal
            total_amount = Decimal(str(invoice.total_amount or 0))
            paid_amount = Decimal(str(invoice.paid_amount or 0))
            
            total_invoice_amount += total_amount
            total_paid_amount += paid_amount
            
            # Determine invoice status and payment timing
            try:
                if invoice.status == 0 and invoice.duedate and invoice.duedate < datetime.date.today():
                    total_overdue_amount += total_amount - paid_amount
                    late_payments += 1
                elif invoice.status == 2:  # Completed
                    on_time_payments += 1
                
                # Outstanding amount calculation
                if invoice.status != 2:  # Not completed
                    # total_outstanding_amount += total_amount - paid_amount
                    total_outstanding_amount = total_invoice_amount - total_paid_amount

            except Exception as e:
                print(f"Error processing invoice {invoice.id}: {e}")

        # Payment Timeliness (35% of score)
        if total_invoices > 0:
            try:
                late_payment_ratio = Decimal(late_payments) / Decimal(total_invoices)
                scoring_components['payment_timeliness'] = max(Decimal('0'), Decimal('100') - (late_payment_ratio * Decimal('100')))
            except Exception as e:
                print(f"Error calculating payment timeliness: {e}")
                scoring_components['payment_timeliness'] = Decimal('100')

        # Payment Consistency (25% of score)
        if payments.count() > 1:
            try:
                payment_amounts = [Decimal(str(p.amount)) for p in payments]
                payment_std = Decimal(str(np.std(payment_amounts)))
                payment_mean = Decimal(str(np.mean(payment_amounts)))
                
                if payment_mean > 0:
                    consistency_score = max(Decimal('0'), Decimal('100') - (payment_std / payment_mean * Decimal('50')))
                    scoring_components['payment_consistency'] = consistency_score
            except Exception as e:
                print(f"Error calculating payment consistency: {e}")

        # Invoice Volume (20% of score)
        if invoices.exists():
            try:
                average_invoice_amount = total_invoice_amount / Decimal(total_invoices) if total_invoices > 0 else Decimal('0')
                scoring_components['invoice_volume'] = min(Decimal('100'), average_invoice_amount / Decimal('10000') * Decimal('100'))
            except Exception as e:
                print(f"Error calculating invoice volume: {e}")

        # Credit Utilization (20% of score)
        credit_limit = Decimal(str(customer.creditlimit or 0))
        if credit_limit > 0:
            try:
                utilization_ratio = (total_outstanding_amount / credit_limit) * Decimal('100')
                scoring_components['credit_utilization'] = max(Decimal('0'), Decimal('100') - min(utilization_ratio, Decimal('100')))
            except Exception as e:
                print(f"Error calculating credit utilization: {e}")

        # Calculate final credit score
        try:
            weighted_score = (
                scoring_components['payment_timeliness'] * Decimal('0.35') +
                scoring_components['payment_consistency'] * Decimal('0.25') +
                scoring_components['invoice_volume'] * Decimal('0.20') +
                scoring_components['credit_utilization'] * Decimal('0.20')
            )

            # Map to standard credit score range (300-850)
            credit_score = int(300 + (weighted_score / Decimal('100') * 550))
        except Exception as e:
            print(f"Error calculating final credit score: {e}")
            credit_score = 500  # Default score if calculation fails

        # Determine credit rating
        def get_credit_rating(score):
            if score >= 800: return "Exceptional"
            if score >= 740: return "Very Good"
            if score >= 670: return "Good"
            if score >= 580: return "Fair"
            return "Poor"

        # Payment Performance Metrics
        payment_performance = {
            'total_invoices': total_invoices,
            'on_time_payments': on_time_payments,
            'late_payments': late_payments,
            'on_time_payment_percentage': (on_time_payments / total_invoices * 100) if total_invoices > 0 else 0,
        }

        # Financial Health Metrics
        financial_health = {
            'total_invoice_amount': float(total_invoice_amount),
            'total_paid_amount': float(total_paid_amount),
            'total_outstanding_amount': float(total_outstanding_amount),
            'total_overdue_amount': float(total_overdue_amount),
            'current_credit_utilization': float((total_outstanding_amount / credit_limit * 100) if credit_limit > 0 else 0),
            'credit_limit': float(credit_limit)
        }

        return {
            "credit_score": credit_score,
            "credit_rating": get_credit_rating(credit_score),
            "scoring_breakdown": {k: float(v) for k, v in scoring_components.items()},
            "customer_id": str(customer.id),
            "customer_name": customer.name,
            "customer_email": customer.email,
            "payment_performance": payment_performance,
            "financial_health": financial_health,
            "analysis": {
                "payment_timeliness": "Reflects the frequency of late payments",
                "payment_consistency": "Measures the variability in payment amounts",
                "invoice_volume": "Indicates the scale of business transactions",
                "credit_utilization": "Shows how much of the credit limit is being used"
            }
        }

    except Exception as e:
        # Catch any unexpected errors
        print(f"Unexpected error in credit score calculation: {e}")
        return {
            "error": f"An unexpected error occurred: {str(e)}",
            "customer_id": str(customer.id)
        }
    
  


def generate_customer_credit_score_report(customer):
    """
    Generate a detailed credit score report for a customer.
    
    Args:
        customer: Customers model instance
    
    Returns:
        dict: A comprehensive credit score report with recommendations
    """
    credit_score_data = calculate_customer_credit_score(customer)
    
    # Generate recommendations
    recommendations = []
    if credit_score_data['credit_rating'] in ['Poor', 'Fair']:
        recommendations = [
            "Make all payments on time",
            "Reduce outstanding invoice amounts",
            "Maintain consistent payment patterns",
            "Avoid maxing out available credit"
        ]
    
    credit_score_data['recommendations'] = recommendations
    
    return credit_score_data







def batch_calculate_customer_credit_scores(customers=None):
    """
    Calculate credit scores for multiple customers.
    
    Args:
        customers: Optional QuerySet of Customers. If None, calculates for all customers.
    
    Returns:
        list: Credit score reports for customers
    """
    from django.apps import apps
    

    # Dynamically import the Customers model
    Customers = apps.get_model('customer', 'Customers')
    
    # If no customers provided, get all active customers
    if customers is None:
        customers = Customers.objects.filter(isactive=True)
    
    credit_scores = []
    for customer in customers:
        try:
            score = calculate_customer_credit_score(customer)
            credit_scores.append(score)
        except Exception as e:
            # Log or handle any errors for individual customers
            credit_scores.append({
                "customer_id": str(customer.id),
                "customer_name": customer.name,
                "error": str(e)
            })
    
    return credit_scores