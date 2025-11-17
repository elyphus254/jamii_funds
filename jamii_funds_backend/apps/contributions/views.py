from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Contribution
from .serializers import ContributionSerializer
from apps.payments.services.stk_push import initiate_stk_push

class ContributionViewSet(viewsets.ModelViewSet):
    queryset = Contribution.objects.all()
    serializer_class = ContributionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only show contributions for user's chamas
        return self.queryset.filter(member=self.request.user)

    def perform_create(self, serializer):
        # Auto-assign member
        serializer.save(member=self.request.user)

    @action(detail=False, methods=['post'])
    def contribute(self, request):
        """
        Custom endpoint: /api/contributions/contribute/
        Body: { "chama_id": 1, "amount": 500, "phone": "254712345678" }
        """
        chama_id = request.data.get('chama_id')
        amount = request.data.get('amount')
        phone = request.data.get('phone')

        if not all([chama_id, amount, phone]):
            return Response({"error": "Missing fields"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            from apps.chamas.models import Chama
            chama = Chama.objects.get(id=chama_id, members=request.user)
        except Chama.DoesNotExist:
            return Response({"error": "Invalid or unauthorized chama"}, status=status.HTTP_400_BAD_REQUEST)

        # Initiate STK Push
        callback_url = f"{request.scheme}://{request.get_host()}/api/payments/c2b/"
        response = initiate_stk_push(phone, amount, f"Contribution to {chama.name}", callback_url)

        if response.get("ResponseCode") == "0":
            # Save pending contribution
            contribution = Contribution.objects.create(
                member=request.user,
                chama=chama,
                amount=amount
            )
            return Response({
                "message": "STK Push sent",
                "checkout_request_id": response["CheckoutRequestID"],
                "contribution_id": contribution.id
            })
        else:
            return Response({"error": "STK Push failed"}, status=status.HTTP_400_BAD_REQUEST)