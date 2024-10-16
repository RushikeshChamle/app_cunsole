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
from .models import SendingStats, EmailConfiguration
from django.core.exceptions import ObjectDoesNotExist
import dns.resolver

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



import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from .models import Domainconfig, DNSRecord

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
        return response['VerificationAttributes'][domain]['VerificationStatus']
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