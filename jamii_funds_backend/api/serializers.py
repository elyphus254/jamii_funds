# api/serializers.py
from rest_framework import serializers
from .models import *

class ChamaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chama
        fields = '__all__'

class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = '__all__'

class ContributionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contribution
        fields = '__all__'

class LoanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = '__all__'

class InterestEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = InterestEntry
        fields = '__all__'

class ProfitDistributionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfitDistribution
        fields = '__all__'