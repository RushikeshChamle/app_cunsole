# import dns.resolver
# from cryptography.hazmat.primitives import serialization
# from cryptography.hazmat.primitives.asymmetric import rsa
# from django.utils import timezone
# from .models import SendingStats, EmailConfiguration
# from cryptography.hazmat.primitives.asymmetric import rsa
# from cryptography.hazmat.backends import default_backend


# from django.core.exceptions import ObjectDoesNotExist
# import dns.resolver

import dns.resolver
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from django.utils import timezone
# from .models import SendingStats, EmailConfiguration
from django.core.exceptions import ObjectDoesNotExist
import dns.resolver


import boto3
from botocore.exceptions import ClientError
from django.conf import settings
# from .models import Domainconfig, DNSRecord

from django.apps import apps
SendingStats = apps.get_model('users', 'SendingStats')
EmailConfiguration = apps.get_model('users', 'EmailConfiguration')
Domainconfig = apps.get_model('users', 'Domainconfig')
DNSRecord = apps.get_model('users', 'DNSRecord')


def verify_spf_record(email_configuration):
    """Verify the SPF record for the given email configuration."""
    try:
        answers = dns.resolver.resolve(email_configuration.domain_name, 'TXT')
        for rdata in answers:
            record = str(rdata)
            if record.startswith('v=spf1'):
                if record == email_configuration.spf_record:
                    email_configuration.is_spf_verified = True
                    email_configuration.save()
                    return 'Valid'
                else:
                    return 'Invalid'
        return 'Not found'
    except dns.resolver.NXDOMAIN:
        return 'Not found'
    except Exception as e:
        return f'Error: {str(e)}'

# Update the existing verify_dns_records function in utils.py
# def verify_dns_records(email_configuration):
#     results = {}
#     # ... existing DKIM verification ...
#     results['spf'] = verify_spf_record(email_configuration)
#     return results

def verify_dns_records(email_configuration):
    results = {}

    # Verify DKIM record
    dkim_record = email_configuration.generate_dkim_record()
    try:
        answers = dns.resolver.resolve(f"{email_configuration.dkim_selector}._domainkey.{email_configuration.domain_name}", 'TXT')
        if any(dkim_record in str(rdata) for rdata in answers):
            results['dkim'] = 'Valid'
        else:
            results['dkim'] = 'Invalid'
    except dns.resolver.NXDOMAIN:
        results['dkim'] = 'DKIM record not found'
    except Exception as e:
        results['dkim'] = f'DKIM verification error: {str(e)}'

    # Verify SPF record
    try:
        answers = dns.resolver.resolve(email_configuration.domain_name, 'TXT')
        spf_record = next((str(rdata) for rdata in answers if str(rdata).startswith('v=spf1')), None)
        if spf_record:
            results['spf'] = 'Valid'
        else:
            results['spf'] = 'SPF record not found'
    except dns.resolver.NXDOMAIN:
        results['spf'] = 'SPF record not found'
    except Exception as e:
        results['spf'] = f'SPF verification error: {str(e)}'

    return results



def generate_dkim_keys():
    """
    Generate a new pair of DKIM (DomainKeys Identified Mail) keys.
    Returns:
        private_pem (str): The private key in PEM format.
        public_pem (str): The public key in PEM format.

    """
    # Generate a new private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    # Convert the private key to PEM format (without encryption)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    # Generate the corresponding public key
    public_key = private_key.public_key()

    # Convert the public key to PEM format
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    # Return both the private and public keys as strings
    return private_pem.decode(), public_pem.decode()





# def verify_dns_records(email_configuration):
#     """
#     Verify the DKIM and SPF DNS records for the given email configuration.
#     Args:
#         email_configuration (object): The email configuration containing domain details.
#     Returns:
#         results (dict): A dictionary with DKIM and SPF validation status.
#     """
#     results = {}

#     # Verify DKIM record
#     dkim_record = email_configuration.generate_dkim_record()
#     try:

#         # Query the DNS for the DKIM record using the domain and selector
#         answers = dns.resolver.resolve(f"{email_configuration.dkim_selector}._domainkey.{email_configuration.domain_name}", 'TXT')

#         # Check if the expected DKIM record is in the DNS response
#         if any(dkim_record in str(rdata) for rdata in answers):
#             results['dkim'] = 'Valid'
#         else:
#             results['dkim'] = 'Invalid'
#     except dns.resolver.NXDOMAIN:

#         # DKIM record not found in DNS
#         results['dkim'] = 'Not found'

#     # Verify SPF record
#     try:

#         # Query the DNS for TXT records of the domain
#         answers = dns.resolver.resolve(email_configuration.domain_name, 'TXT')

#         # Look for the SPF record that starts with 'v=spf1
#         spf_record = next((str(rdata) for rdata in answers if str(rdata).startswith('v=spf1')), None)
#         if spf_record:
#             results['spf'] = 'Valid'
#         else:
#             results['spf'] = 'Not found'
#     except dns.resolver.NXDOMAIN:

#         # SPF record not found in DNS
#         results['spf'] = 'Not found'

#     return results


def verify_dns_records(email_configuration):
    results = {}

    # Verify DKIM record
    dkim_record = email_configuration.generate_dkim_record()
    print(f"Checking DKIM record for {dkim_record}...")
    try:
        answers = dns.resolver.resolve(f"{email_configuration.dkim_selector}._domainkey.{email_configuration.domain_name}", 'TXT')
        print(f"DKIM DNS response: {answers}")
        if any(dkim_record in str(rdata) for rdata in answers):
            results['dkim'] = 'Valid'
        else:
            results['dkim'] = 'Invalid'
    except dns.resolver.NXDOMAIN:
        results['dkim'] = 'DKIM record not found'
    except Exception as e:
        results['dkim'] = f'DKIM verification error: {str(e)}'

    # Verify SPF record
    print(f"Checking SPF record for {email_configuration.domain_name}...")
    try:
        answers = dns.resolver.resolve(email_configuration.domain_name, 'TXT')
        print(f"SPF DNS response: {answers}")
        spf_record = next((str(rdata) for rdata in answers if str(rdata).startswith('v=spf1')), None)
        if spf_record:
            results['spf'] = 'Valid'
        else:
            results['spf'] = 'SPF record not found'
    except dns.resolver.NXDOMAIN:
        results['spf'] = 'SPF record not found'
    except Exception as e:
        results['spf'] = f'SPF verification error: {str(e)}'

    return results



def verify_dmarc_record(email_configuration):

    """
    Verify the DMARC DNS record for the given email configuration.
    Args:
        email_configuration (object): The email configuration containing domain details.
    Returns:
        bool: True if the DMARC record is valid, otherwise False.
    """
    try:
        # Query the DNS for the DMARC record of the domain
        answers = dns.resolver.resolve(f"_dmarc.{email_configuration.domain_name}", 'TXT')
        expected_record = email_configuration.generate_dmarc_record()
        for rdata in answers:
            # Check if the expected DMARC record is in the DNS response

            if expected_record in str(rdata):
                email_configuration.is_dmarc_verified = True
                email_configuration.save()
                return True
        return False
    except dns.resolver.NXDOMAIN:
        # DMARC record not found in DNS
        return False



def check_sending_limit(email_configuration):

    """
    Check if the email configuration has reached its daily sending limit.
    Args:
        email_configuration (object): The email configuration containing user settings.
    Returns:
        bool: True if the sending limit has not been exceeded, otherwise False.

    
    """
    today = timezone.now().date()
    stats, created = SendingStats.objects.get_or_create(
        email_configuration=email_configuration,
        date=today
    )
    return stats.emails_sent < email_configuration.daily_send_limit



def increment_sent_emails(email_configuration):

    """
    Increment the number of emails sent for the email configuration.
    Args:
        email_configuration (object): The email configuration containing user settings.
    """
    today = timezone.now().date()
    # Retrieve or create the sending statistics for the given configuration and date
    stats, created = SendingStats.objects.get_or_create(
        email_configuration=email_configuration,
        date=today
    )
    stats.emails_sent += 1
    stats.save()




from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def send_test_email(email_configuration):
    """
    Send a test email to verify the email configuration.
    Args:
        email_configuration (object): The email configuration containing user details.
    Returns:
        tuple: (bool, str) True if the email was sent successfully, otherwise False with an error message.

    """
    subject = f'Test Email from {email_configuration.domain_name}'
    # html_message = render_to_string('test_email_template.html', {
    html_message = render_to_string('app_cunsole/users/templates/test_email_template.html', {
        'domain': email_configuration.domain_name,
        'dkim_selector': email_configuration.dkim_selector,
        'spf_record': email_configuration.spf_record,
        'dmarc_record': email_configuration.dmarc_record,
    })
    plain_message = strip_tags(html_message)
    from_email = f'test@{email_configuration.domain_name}'
    to_email = email_configuration.user.email

    try:
        send_mail(
            subject,
            plain_message,
            from_email,
            [to_email],
            html_message=html_message,
            fail_silently=False,
        )
        return True, "Test email sent successfully"
    except Exception as e:
        return False, str(e)





def create_ses_client():
    return boto3.client('ses', 
                        region_name=settings.AWS_REGION,
                        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)

def add_domain_to_ses(domain):
    ses_client = create_ses_client()
    try:
        # Verify domain identity
        ses_client.verify_domain_identity(Domain=domain)

        # Generate DKIM tokens
        dkim_tokens = ses_client.verify_domain_dkim(Domain=domain)['DkimTokens']

        # Set MAIL FROM domain
        mail_from_domain = f"mail.{domain}"
        ses_client.set_identity_mail_from_domain(
            Identity=domain,
            MailFromDomain=mail_from_domain
        )

        return {
            'dkim_tokens': dkim_tokens,
            'mail_from_domain': mail_from_domain
        }
    except ClientError as e:
        print(f"Error adding domain to SES: {e}")
        return None

def get_verification_status(domain):
    ses_client = create_ses_client()
    try:
        response = ses_client.get_identity_verification_attributes(
            Identities=[domain]
        )
        return response.VerificationAttributes[domain].VerificationStatus
    except ClientError as e:
        print(f"Error getting verification status: {e}")
        return None


def generate_dns_records(domain, dkim_tokens, mail_from_domain):
    records = []

    # DKIM records
    for token in dkim_tokens:
        records.append({
            'record_type': 'DKIM',
            'name': f"{token}._domainkey.{domain}",
            'value': f"{token}.dkim.amazonses.com",
            'selector': token
        })

    # SPF record
    records.append({
        'record_type': 'TXT',
        'name': domain,
        'value': "v=spf1 include:amazonses.com ~all"
    })

    # DMARC record
    records.append({
        'record_type': 'TXT',
        'name': f"_dmarc.{domain}",
        'value': "v=DMARC1; p=none;"
    })

    # MAIL FROM MX record
    records.append({
        'record_type': 'MX',
        'name': mail_from_domain,
        'value': f"10 feedback-smtp.{settings.AWS_REGION}.amazonses.com"
    })

    # MAIL FROM SPF record
    records.append({
        'record_type': 'TXT',
        'name': mail_from_domain,
        'value': "v=spf1 include:amazonses.com ~all"
    })

    return records


# from openai import OpenAI
# from django.conf import settings

# # Initialize the OpenAI client
# client = OpenAI(api_key=settings.OPENAI_API_KEY)

# import logging

# def generate_email(subject, customer_name, due_date, invoice_amount):
#     prompt = f"""
#     Create a professional and polite payment reminder email.
#     - Subject: {subject}
#     - Customer Name: {customer_name}
#     - Invoice Amount: {invoice_amount}
#     - Due Date: {due_date}
#     The tone should be friendly but firm, encouraging timely payment.
#     """
#     logging.debug("Generated prompt: %s", prompt)

#     # Using the ChatCompletion method for the gpt-3.5-turbo model
#     response = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[
#             {"role": "user", "content": prompt}
#         ],
#         max_tokens=200,
#         temperature=0.7,
#     )

#     if 'choices' not in response or not response['choices']:
#         raise ValueError("Invalid response from OpenAI API")

#     return response['choices'][0]['message']['content'].strip()




import openai
from django.conf import settings
from openai import AzureOpenAI

class AzureOpenAIService:
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_KEY,
            api_version=settings.AZURE_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )

    def generate_response(self, prompt, max_tokens=500):
        try:
            response = self.client.chat.completions.create(
                model=settings.AZURE_DEPLOYMENT_NAME,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7,
            )
            return {
                'status': 'success',
                'data': response.choices[0].message.content
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
        

    # def generate_trigger_email(
    #     self, tone, style, length, include_greeting, include_salutation, 
    #     placeholders, max_tokens=500
    # ):
    #     try:
    #         # Build the email prompt using the provided parameters
    #         email_prompt = (
    #             f"Generate an email for accounts receivable automation:\n"
    #             f"Tone: {tone}\n"
    #             f"Style: {style}\n"
    #             f"Length: {length}\n"
    #         )
    #         if include_greeting:
    #             email_prompt += "Include a greeting.\n"
    #         if include_salutation:
    #             email_prompt += "Include a salutation.\n"

    #         # Add placeholders directly to the prompt in the required format
    #         email_prompt += (
    #             "Use the following placeholders exactly as provided:\n"
    #             f"{', '.join(placeholders)}\n"
    #             "Ensure these placeholders remain in the email as-is.\n"
    #         )

    #         # Call Azure OpenAI to generate the email
    #         response = self.client.chat.completions.create(
    #             model=settings.AZURE_DEPLOYMENT_NAME,
    #             messages=[{"role": "user", "content": email_prompt}],
    #             max_tokens=max_tokens,
    #             temperature=0.7,
    #         )

    #         # Extract subject and body from the response
    #         email_content = response.choices[0].message.content.strip()
    #         subject, body = email_content.split('\n', 1)

    #         # No replacement needed, placeholders remain as-is
    #         return {
    #             'status': 'success',
    #             'subject': subject.strip(),
    #             'body': body.strip()
    #         }

    #     except Exception as e:
    #         return {'status': 'error', 'message': str(e)}

    def generate_trigger_email(
        self, tone, style, length, include_greeting, include_salutation, 
        placeholders, max_tokens=500
):
     try:
        # Build a more refined and specific email prompt
        email_prompt = (
            f"Generate a professional email for accounts receivable teams to use as a payment reminder:\n"
            f"- Tone: {tone}\n"
            f"- Style: {style}\n"
            f"- Length: {length}\n"
            f"- Purpose: Remind customers about outstanding invoices to encourage timely payments.\n"
            f"- Ensure a polite, professional, and customer-friendly tone.\n"
        )
        
        if include_greeting:
            email_prompt += "- Begin the email with a friendly but professional greeting.\n"
        if include_salutation:
            email_prompt += "- Conclude with a polite closing and salutation.\n"

        # Ensure placeholders are included in the email body and subject
        email_prompt += (
            "- Use the following placeholders **exactly as provided** in both the subject and body:\n"
            f"{', '.join(placeholders)}\n"
            "- These placeholders must remain unchanged in the final email.\n"
            "- Include a relevant subject line (e.g., 'Reminder: Invoice {Invoice.Name} Due Soon').\n"
            "- Provide clear invoice details using placeholders.\n"
        )

        # Call Azure OpenAI to generate the email content
        response = self.client.chat.completions.create(
            model=settings.AZURE_DEPLOYMENT_NAME,
            messages=[{"role": "user", "content": email_prompt}],
            max_tokens=max_tokens,
            temperature=0.7,
        )

        # Extract subject and body from the response
        email_content = response.choices[0].message.content.strip()
        subject, body = email_content.split('\n', 1)

        # Return the generated email with placeholders intact
        return {
            'status': 'success',
            'subject': subject.strip(),
            'body': body.strip()
        }

     except Exception as e:
        return {'status': 'error', 'message': str(e)}




from openai import AzureOpenAI
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class EmailGenerator:
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_KEY,
            api_version=settings.AZURE_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )

    def _create_prompt(self, subject, customer_name, due_date, invoice_amount):
        prompt = f"""
        Create a professional and polite payment reminder email with the following details:
        
        REQUIREMENTS:
        - Subject: {subject}
        - Customer Name: {customer_name}
        - Invoice Amount: {invoice_amount}
        - Due Date: {due_date}
        
        GUIDELINES:
        - Tone should be professional and courteous
        - Include clear payment instructions
        - Mention the invoice details
        - End with a professional signature
        - Format with proper spacing and paragraphs
        
        Please format the response as:
        SUBJECT: [Email Subject]
        
        [Email Body]
        """
        logger.debug("Generated prompt: %s", prompt)
        return prompt

    def generate_email(self, subject, customer_name, due_date, invoice_amount):
        try:
            prompt = self._create_prompt(
                subject=subject,
                customer_name=customer_name,
                due_date=due_date,
                invoice_amount=invoice_amount
            )

            response = self.client.chat.completions.create(
                model=settings.AZURE_DEPLOYMENT_NAME,
                messages=[
                    {"role": "system", "content": "You are a professional accounts receivable specialist crafting payment reminder emails."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7,
            )

            generated_text = response.choices[0].message.content.strip()
            
            # Log successful generation
            logger.info(f"Successfully generated email for customer: {customer_name}")
            
            return generated_text

        except Exception as e:
            logger.error(f"Error generating email: {str(e)}", exc_info=True)
            raise


