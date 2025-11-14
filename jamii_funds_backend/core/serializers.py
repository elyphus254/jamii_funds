from rest_framework import serializers
from .models import Chama, Member, Loan

class ChamaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chama
        fields = '__all__'

class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = '__all__'

class LoanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = '__all__'
