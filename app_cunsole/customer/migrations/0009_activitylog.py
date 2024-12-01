# Generated by Django 5.0.8 on 2024-11-06 19:10

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0008_communicationtemplate_communicationlog_dispute_task_and_more'),
        ('invoices', '0009_alter_invoices_paid_amount_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ActivityLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('activity_type', models.IntegerField(choices=[(0, 'Invoice Created'), (1, 'Invoice Updated'), (2, 'Invoice Status Changed'), (3, 'Payment Created'), (4, 'Payment Updated'), (5, 'Email Trigger Created'), (6, 'Email Trigger Updated'), (7, 'Email Sent'), (8, 'Other')])),
                ('email_subject', models.CharField(blank=True, max_length=255, null=True)),
                ('email_description', models.CharField(blank=True, max_length=255, null=True)),
                ('email_from', models.EmailField(blank=True, max_length=254, null=True)),
                ('email_to', models.TextField(blank=True, null=True)),
                ('email_cc', models.TextField(blank=True, null=True)),
                ('email_bcc', models.TextField(blank=True, null=True)),
                ('email_status', models.IntegerField(blank=True, choices=[(0, 'Sent'), (1, 'Failed'), (2, 'Pending')], null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_disabled', models.BooleanField(default=False)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activity_logs', to='customer.account')),
                ('email_trigger', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='customer.emailtrigger')),
                ('invoice', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='invoices.invoices')),
                ('payment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='invoices.payment')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'activity_logs',
            },
        ),
    ]