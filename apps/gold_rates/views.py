from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Rate

class RateDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        rate = Rate.get_current()
        return Response({
            "gold_price": rate.gold_price,
            "forex_rate": rate.forex_rate
        })
        
    def post(self, request):
        rate = Rate.get_current()
        rate.gold_price = request.data.get('gold_price', rate.gold_price)
        rate.forex_rate = request.data.get('forex_rate', rate.forex_rate)
        rate.save()
        return Response({
            "gold_price": rate.gold_price,
            "forex_rate": rate.forex_rate
        })
