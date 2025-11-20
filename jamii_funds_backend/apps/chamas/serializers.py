# chamas/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Chama, Member

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id',  'email', 'first_name', 'last_name')

class MemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='user', write_only=True, required=False
    )

    class Meta:
        model = Member
        fields = ('id', 'user', 'user_id', 'role', 'joined_at')
        read_only_fields = ('joined_at',)

class ChamaListSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()
    is_member = serializers.SerializerMethodField()
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = Chama
        fields = ('id', 'name', 'description', 'created_by', 'created_at', 'member_count', 'is_member')

    def get_member_count(self, obj):
        return obj.membership.count()

    def get_is_member(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.membership.filter(user=request.user).exists()
        return False

class ChamaDetailSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    members = MemberSerializer(source='membership', many=True, read_only=True)
    member_count = serializers.SerializerMethodField()
    is_member = serializers.SerializerMethodField()
    current_user_role = serializers.SerializerMethodField()

    class Meta:
        model = Chama
        fields = ('id', 'name', 'description', 'created_by', 'created_at',
                  'members', 'member_count', 'is_member', 'current_user_role')

    def get_member_count(self, obj):
        return obj.membership.count()

    def get_is_member(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.membership.filter(user=request.user).exists()
        return False

    def get_current_user_role(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            membership = obj.membership.filter(user=request.user).first()
            return membership.role if membership else None
        return None

class ChamaCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chama
        fields = ('name', 'description')