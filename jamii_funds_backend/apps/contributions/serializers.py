from rest_framework import serializers
from .models import Contribution
from apps.payments.serializers import MpesaTransactionSerializer

class ContributionSerializer(serializers.ModelSerializer):
    member = serializers.ReadOnlyField(source='member.username')
    chama = serializers.ReadOnlyField(source='chama.name')
    mpesa_transaction = MpesaTransactionSerializer(read_only=True)

    class Meta:
        model = Contribution
        fields = [
            'id', 'member', 'chama', 'amount',
            'mpesa_transaction', 'contributed_at', 'is_verified'
        ]
        read_only_fields = ['contributed_at', 'is_verified']