# Generated by Django 5.0.8 on 2024-10-18 21:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0006_customers_account_balance_customers_crm_id_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Contact',
            new_name='Customer_contact',
        ),
        migrations.AlterModelTable(
            name='customer_contact',
            table='cust_contacts',
        ),
    ]