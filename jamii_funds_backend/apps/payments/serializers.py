from rest_framework import serializers
#from .models import Payment, Loan, LoanRepayment
from apps.chamas.models import Member


class PaymentSerializer(serializers.ModelSerializer):
    member = serializers.StringRelatedField()
    member_id = serializers.PrimaryKeyRelatedField(
        queryset=Member.objects.all(), source='member', write_only=True
    )

    class Meta:
        #model = Payment
        fields = [
            'id',
            'member', 'member_id',
            'phone_number',
            'amount',
            'checkout_request_id',
            'merchant_request_id',
            'status',
            'created_at',
        ]
        read_only_fields = ['id', 'status', 'created_at']
