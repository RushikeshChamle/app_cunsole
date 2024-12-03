# import json
# from users.utils import AzureOpenAIService
# from users.context_helpers import extract_relevant_context
# from customer.models import AIInteraction


# from django.contrib.auth import get_user_model
# User = get_user_model()



# def generate_ai_response(user, account, user_query):
#     context = extract_relevant_context(account)
#     prompt = f"""
#     Context: {json.dumps(context)}
#     User Query: {user_query}
#     Provide a professional response leveraging the above context.
#     """
#     azure_openai_service = AzureOpenAIService()

#     try:
#         response = azure_openai_service.generate_response(prompt)
#         if response['status'] == 'success':
#             ai_response = response['data']
#             log_ai_interaction(user, account, user_query, ai_response)
#             return ai_response
#         else:
#             return f"Error: {response['message']}"
#     except Exception as e:
#         return f"An error occurred: {str(e)}"

# def log_ai_interaction(user, account, query, response):
#     AIInteraction.objects.create(user=user, account=account, query=query, response=response)




import json
# from users.utils import AzureOpenAIService
from app_cunsole.users.utils import AzureOpenAIService

from app_cunsole.users.utils import AzureOpenAIService
from app_cunsole.users.context_helpers import extract_relevant_context


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
