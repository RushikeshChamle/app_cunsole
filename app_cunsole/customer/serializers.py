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



class EmailTriggerSerializer(serializers.ModelSerializer):
    # condition_type_display = serializers.CharField(source='get_condition_type_display', read_only=True)

    class Meta:
        model = EmailTrigger
        fields = '__all__'
