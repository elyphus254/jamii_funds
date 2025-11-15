# core/serializers.py
from rest_framework import serializers
from .models import Chama, Member, Loan, Contribution

class ChamaSerializer(serializers.ModelSerializer):
    member_count = serializers.IntegerField(source='members.count', read_only=True)
    total_pool = serializers.DecimalField(source='total_contributions', max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = Chama
        fields = ['id', 'name', 'description', 'till_number', 'created_by', 'created_at', 'member_count', 'total_pool']
        read_only_fields = ['created_by']

class MemberSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    chama_name = serializers.CharField(source='chama.name', read_only=True)

    class Meta:
        model = Member
        fields = ['id', 'user', 'chama', 'chama_name', 'joined_date', 'is_admin']

class ContributionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contribution
        fields = ['id', 'amount', 'date', 'transaction_ref', 'confirmed']

class LoanApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = ['amount', 'tenure_months', 'interest_rate']
        extra_kwargs = {'interest_rate': {'required': False}}

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be positive")
        return value

class LoanSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.user.get_full_name', read_only=True)
    chama = serializers.CharField(source='member.chama.name', read_only=True)
    total_repayable = serializers.SerializerMethodField()

    class Meta:
        model = Loan
        fields = ['id', 'member', 'member_name', 'chama', 'amount', 'interest_rate',
                  'tenure_months', 'status', 'applied_date', 'total_repayable']
        read_only_fields = ['status', 'applied_date']

    def get_total_repayable(self, obj):
        return obj.total_repayable