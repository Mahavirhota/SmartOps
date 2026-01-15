from rest_framework import serializers
from django.contrib.auth import get_user_model
from .utils import generate_random_password

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class PasswordSuggestionSerializer(serializers.Serializer):
    length = serializers.IntegerField(required=False, default=12, min_value=8, max_value=64)
    password = serializers.CharField(read_only=True)
