from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from app_cunsole.customer.models import Account

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"  # Include all fields in the serialized data




class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        refresh = self.get_token(self.user)

        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)

        # You can add more user-specific data here if needed
        data["user"] = {
            "id": self.user.id,
            "name": self.user.name,
            "email": self.user.email,
        }

        return data


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = "__all__"  # Include all fields in the serialized data


class UserdataSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "name",
            "email",
            "password",
            "contact",
            "is_active",
            "created_at",
        ]
        extra_kwargs = {
            "password": {"write_only": True},
        }

    def create(self, validated_data):
        user = User(
            email=validated_data["email"],
            name=validated_data["name"],
            contact=validated_data["contact"],
            is_active=validated_data.get("is_active", True),
        )
        user.set_password(validated_data["password"])
        user.save()
        return user

    def update(self, instance, validated_data):
        instance.email = validated_data.get("email", instance.email)
        instance.name = validated_data.get("name", instance.name)
        instance.contact = validated_data.get("contact", instance.contact)
        instance.is_active = validated_data.get("is_active", instance.is_active)
        if "password" in validated_data:
            instance.set_password(validated_data["password"])
        instance.save()
        return instance


class UserCreationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    name = serializers.CharField(required=False)
    contact = serializers.CharField(required=False, max_length=15)
    account_id = serializers.IntegerField()
