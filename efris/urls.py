from django.urls import path
from . import views
from .views import billing_upload
from .views import download_invoice_pdf
from .views import upload_invoice_to_efris



urlpatterns = [
   
    path('billing-upload/', billing_upload, name='billing_upload'),
    path('dash/', views.dashboard, name='dashboard'),
    path('', views.landing, name='landing'),
    path('generate-receipt/', views.generate_receipt, name='generate_receipt'),
    path('download-invoice/', download_invoice_pdf, name='download_invoice_pdf'),
  
    path('invoice/query/', views.fetch_invoice_t108, name='fetch_invoice_t108'),

    path('upload_invoice_to_efris/', upload_invoice_to_efris, name='upload_invoice_to_efris'),
    path('save-invoice-session/', views.save_invoice_session, name='save_invoice_session'),
    


    
    
]

