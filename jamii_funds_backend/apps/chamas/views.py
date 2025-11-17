from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Chama
from .serializers import ChamaSerializer

class ChamaViewSet(viewsets.ModelViewSet):
    queryset = Chama.objects.all()
    serializer_class = ChamaSerializer
    permission_classes = [IsAuthenticated]