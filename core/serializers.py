from rest_framework import serializers

class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    recaptcha = serializers.CharField(write_only=True)

class RegisterVerifySerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6)

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class LoginVerifySerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6)