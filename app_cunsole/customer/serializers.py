from rest_framework import serializers

from .models import Customers, EmailTrigger




class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customers
        fields = "__all__"



class EmailTriggerSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailTrigger
        fields = '__all__'
