from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        validators=[validate_password]
    )
    password2 = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "phone",
            "password",
            "password2",
            "first_name",
            "last_name",
        ]

    def validate(self, attrs):
        # Check password match
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Passwords do not match."})

        # Unique email
        if User.objects.filter(email=attrs["email"]).exists():
            raise serializers.ValidationError({"email": "Email already exists."})

        # Unique phone
        phone = attrs.get("phone")
        if phone and User.objects.filter(phone=phone).exists():
            raise serializers.ValidationError({"phone": "Phone number already registered."})

        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        user = User.objects.create_user(**validated_data)
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "phone",
            "first_name",
            "last_name",
            "is_phone_verified",
        ]
        read_only_fields = ["id", "is_phone_verified"]
