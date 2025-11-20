# apps/chamas/views.py

from django.db import connection
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication, TokenAuthentication

from .models import Chama, Member
from .serializers import (
    ChamaListSerializer,
    ChamaDetailSerializer,
    ChamaCreateUpdateSerializer,
    MemberSerializer
)
from .permissions import IsAdminMember, IsCreatorOrAdmin


class ChamaViewSet(viewsets.ModelViewSet):
    queryset = Chama.objects.all().order_by('-created_at')
    authentication_classes = [TokenAuthentication]
    permission_classes = []
    lookup_field = 'pk'

    def get_serializer_class(self):
        if self.action == 'list':
            return ChamaListSerializer
        if self.action == 'retrieve':
            return ChamaDetailSerializer
        return ChamaCreateUpdateSerializer
    
    def list(self, request, *args, **kwargs):
        print("=== LIST ACTION DEBUG ===")
        print(f"User: {request.user}")
        print(f"User authenticated: {request.user.is_authenticated}")
        print(f"User email: {getattr(request.user, 'email', 'No email')}")
        print(f"Action: {self.action}")
        print(f"Permissions: {self.get_permissions()}")
        print("AUTH HEADER:", request.headers.get("Authorization"))
        print("USER:", request.user)
        print("AUTHENTICATED:", request.user.is_authenticated)

        # Check current schema
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_schema();")
            schema = cursor.fetchone()[0]
            print(f"Current schema: {schema}")
        
        # Make sure to return the super() call
        response = super().list(request, *args, **kwargs)
        print(f"Response status: {response.status_code}")
        return response
    

    def get_permissions(self):
        """
        Fix permissions to allow GET requests for authenticated users
        """
        if self.action == 'create':
            return [IsAuthenticated()]
        elif self.action in ['list', 'retrieve']:  # Allow GET for list and detail
            return [IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsCreatorOrAdmin()]
        elif self.action in ['join', 'leave']:
            return [IsAuthenticated()]
        elif self.action == 'members':
            return [IsAdminMember()]
        else:
            return [IsAuthenticated()]




    def create(self, request, *args, **kwargs):
        print("=== API CREATE DEBUG ===")
        
        # Debug: Check current schema
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_schema();")
            schema = cursor.fetchone()[0]
            print(f"Current schema: {schema}")
        
        # Debug: Check if table exists in current schema
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = %s AND table_name = 'chamas_chama'
            """, [schema])
            
            if cursor.fetchone():
                print(f"✓ chamas_chama exists in {schema}")
            else:
                print(f"✗ chamas_chama does NOT exist in {schema}")
                # List available tables
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = %s
                    ORDER BY table_name
                """, [schema])
                tables = [t[0] for t in cursor.fetchall()]
                print(f"Available tables in {schema}: {tables}")
        
        print("=== END DEBUG ===")
        
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        print("=== PERFORM_CREATE DEBUG ===")
        print(f"User: {self.request.user.email}")
        print(f"User ID: {self.request.user.id}")
        
        # Check if user exists in current schema
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user_exists = User.objects.filter(id=self.request.user.id).exists()
        print(f"User exists in current schema: {user_exists}")
        
        chama = serializer.save(created_by=self.request.user)
        Member.objects.create(user=self.request.user, chama=chama, role='admin')
        print(f"✓ Created chama: {chama.name}")
        print("=== END PERFORM_CREATE DEBUG ===")

    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        chama = self.get_object()
        membership, created = Member.objects.get_or_create(
            user=request.user, chama=chama, defaults={'role': 'member'}
        )
        if not created:
            return Response({"detail": "Already a member"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": f"Joined {chama.name} successfully"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        chama = self.get_object()
        if chama.created_by == request.user:
            return Response({"detail": "Creator cannot leave their own chama"}, status=status.HTTP_400_BAD_REQUEST)

        deleted = Member.objects.filter(user=request.user, chama=chama).delete()
        if deleted[0] == 0:
            return Response({"detail": "Not a member"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": f"Left {chama.name}"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get', 'patch'], permission_classes=[IsAdminMember])
    def members(self, request, pk=None):
        chama = self.get_object()
        if request.method == 'GET':
            members = chama.membership.all()
            serializer = MemberSerializer(members, many=True)
            return Response(serializer.data)

        user_id = request.data.get('user_id')
        role = request.data.get('role')
        if not user_id or role not in ['member', 'admin']:
            return Response({"detail": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            member = chama.membership.get(user_id=user_id)
            member.role = role
            member.save()
            return Response(MemberSerializer(member).data)
        except Member.DoesNotExist:
            return Response({"detail": "Member not found"}, status=status.HTTP_404_NOT_FOUND)