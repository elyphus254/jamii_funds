# apps/auth_app/views.py

from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token

User = get_user_model()


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Register a new user using EMAIL as the unique identifier
    POST /api/auth/register/
    {
        "email": " : "john@example.com",
        "password": "supersecret123",
        "first_name": "John",
        "last_name": "Doe"
    }
    """
    email = request.data.get('email')
    password = request.data.get('password')
    first_name = request.data.get('first_name', '')
    last_name = request.data.get('last_name', '')

    if not email or not password:
        return Response({
            'error': 'Email and password are required'
        }, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email__iexact=email).exists():
        return Response({
            'error': 'A user with that email already exists'
        }, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(
        email=email.lower(),
        password=password,
        first_name=first_name,
        last_name=last_name,
    )

    token, _ = Token.objects.get_or_create(user=user)

    return Response({
        'success': True,
        'message': 'User registered successfully!',
        'user': {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        },
        'token': token.key
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Login with email + password → returns token
    POST /api/auth/login/
    {
        "email": "john@example.com",
        "password": "supersecret123"
    }
    """
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response({
            'error': 'Email and password are required'
        }, status=status.HTTP_400_BAD_REQUEST)

    # authenticate() works with your custom user model automatically
    user = authenticate(request, email=email, password=password)

    if not user:
        return Response({
            'error': 'Invalid credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)

    token, _ = Token.objects.get_or_create(user=user)

    return Response({
        'success': True,
        'token': token.key,
        'user': {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }
    }, status=status.HTTP_200_OK)