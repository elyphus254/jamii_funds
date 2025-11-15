# auth_app/urls.py
"""
Authentication endpoints for Jamii Funds.

Public:
  POST  /auth/register/  → create user + JWT
  POST  /auth/login/     → JWT pair
  POST  /auth/refresh/   → refresh access token

Protected:
  GET   /auth/profile/   → current user
  POST  /auth/logout/    → blacklist refresh token
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    register_user,
    login_user,
    profile_user,
    logout_user,  # ← add this view
)

urlpatterns = [
    # ------------------------------------------------------------------
    # Public: Registration & Login
    # ------------------------------------------------------------------
    path('register/', register_user, name='register'),
    path('login/', login_user, name='login'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # ------------------------------------------------------------------
    # Protected: Profile & Logout
    # ------------------------------------------------------------------
    path('profile/', profile_user, name='profile'),
    path('logout/', logout_user, name='logout'),
]
