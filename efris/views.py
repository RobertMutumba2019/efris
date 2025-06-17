from django.shortcuts import render

# Create your views here.
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Invoice
from .serializers import InvoiceSerializer
from django.shortcuts import render

class InvoiceAPIView(APIView):
    def get(self, request):
        invoices = Invoice.objects.all().order_by('-created_at')
        serializer = InvoiceSerializer(invoices, many=True)
        return Response(serializer.data)

def landing_page(request):
    invoices = Invoice.objects.all().order_by('-created_at')
    return render(request, 'landing.html', {'invoices': invoices})
