# Generated by Django 5.0.8 on 2024-10-13 11:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_domainconfig_is_default_domainconfig_send_mail_from_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='domainconfig',
            old_name='send_mail_from',
            new_name='mailing_address',
        ),
    ]