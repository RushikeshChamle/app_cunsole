# Generated by Django 5.0.8 on 2024-10-20 11:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0007_invoices_avatax_tax_code_invoices_avatax_use_code_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='invoicedetails',
            old_name='discount',
            new_name='discount_amount',
        ),
        migrations.AddField(
            model_name='invoicedetails',
            name='discount_percentage',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='invoices',
            name='discount_amount',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='invoices',
            name='discount_percentage',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
    ]
