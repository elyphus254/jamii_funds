from rest_framework import serializers
from .models import ContributionType, Contribution
from apps.chamas.models import Member


class ContributionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContributionType
        fields = ['id', 'name', 'description', 'default_amount', 'is_fixed']
        read_only_fields = ['id']


class ContributionSerializer(serializers.ModelSerializer):
    member = serializers.StringRelatedField()
    member_id = serializers.PrimaryKeyRelatedField(
        queryset=Member.objects.all(), source='member', write_only=True
    )

    type = serializers.StringRelatedField()
    type_id = serializers.PrimaryKeyRelatedField(
        queryset=ContributionType.objects.all(), source='type', write_only=True
    )

    class Meta:
        model = Contribution
        fields = [
            'id',
            'member', 'member_id',
            'type', 'type_id',
            'amount',
            'date',
            'reference'
        ]
        read_only_fields = ['id', 'date']