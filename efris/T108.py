import json
import uuid
import base64
import requests
from datetime import datetime
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse


def generate_request_payload(invoice_no, tin, device_no):
    """
    Mock encryption: encodes the invoice payload in base64 as EFRIS expects
    """
    payload = {
        "invoiceNo": invoice_no
    }

    encrypted_content = base64.b64encode(json.dumps(payload).encode()).decode()

    return {
        "data": {
            "content": encrypted_content,
            "signature": "",  # Add signature logic here if needed
            "dataDescription": {
                "codeType": "0",
                "encryptCode": "1",
                "zipCode": "0"
            }
        },
        "globalInfo": {
            "appId": "AP01",
            "version": "1.1.20191201",
            "dataExchangeId": str(uuid.uuid4()).replace("-", ""),
            "interfaceCode": "T108",
            "requestCode": "TP",
            "requestTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "responseCode": "TA",
            "userName": "admin",
            "deviceMAC": "FFFFFFFFFFFF",
            "deviceNo": device_no,
            "tin": tin,
            "extendField": {}
        },
        "returnStateInfo": {
            "returnCode": "",
            "returnMessage": ""
        }
    }


@csrf_exempt
def fetch_invoice_from_efris(request):
    if request.method == 'POST':
        invoice_no = request.POST.get('invoiceNo')
        if not invoice_no:
            return JsonResponse({"status": "error", "message": "Invoice number is required"}, status=400)

        # Provide your actual TIN and device number here
        tin = "1003118023"
        device_no = "TCS085e154266969073"

        payload = generate_request_payload(invoice_no, tin, device_no)

        try:
            url = "https://efristest.ura.go.ug/efrisws/uws/queryInvoice"  # EFRIS test endpoint
            headers = {'Content-Type': 'application/json'}

            response = requests.post(url, data=json.dumps(payload), headers=headers)

            if response.status_code == 200:
                res_data = response.json()

                content_base64 = res_data.get("data", {}).get("content", "")
                decoded_json = base64.b64decode(content_base64).decode()

                invoice_data = json.loads(decoded_json)

                return render(request, 'search_invoice.html', {
                    'invoice': invoice_data
                })
            else:
                return JsonResponse({"status": "error", "message": "Failed to connect to URA"}, status=500)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    # Initial GET request
    return render(request, 'search_invoice.html')
