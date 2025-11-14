from rest_framework import serializers
from core.models import Chama, Member, Contribution, Loan, InterestEntry, ProfitDistribution
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]

class ChamaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chama
        fields = "__all__"

class MemberSerializer(serializers.ModelSerializer):
    person_name = serializers.CharField(source="person.username", read_only=True)

    class Meta:
        model = Member
        fields = "__all__"

class ContributionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contribution
        fields = "__all__"

class LoanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = "__all__"

class InterestEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = InterestEntry
        fields = "__all__"

class ProfitDistributionSerializer(serializers.ModelSerializer):
    chama_name = serializers.CharField(source="chama.name", read_only=True)

    class Meta:
        model = ProfitDistribution
        fields = [
            "id", "chama", "chama_name", "period_start", "period_end",
            "total_interest_collected", "computed", "results", "created_at"
        ]
        read_only_fields = ["computed", "results", "total_interest_collected"]
