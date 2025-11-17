from rest_framework import serializers
from .models import Chama

class ChamaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chama
        fields = "__all__"
        read_only_fields = ["created_by", "created_at"]