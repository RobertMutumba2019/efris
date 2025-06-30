from io import BytesIO
from .models import InvoiceRecord
import qrcode
import requests
import uuid
import json
import base64
from datetime import datetime
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa

@csrf_exempt
def fetch_invoice_t108(request):
    if request.method == 'POST':
        invoice_no = request.POST.get('invoiceNo') or request.session.get('last_uploaded_invoice_no')
        device_no = request.session.get('device_no', 'TCS085e154266969073')  # fallback

        if not invoice_no:
            return JsonResponse({"status": "error", "message": "Invoice number is required"}, status=400)

        tin = "1003118023"  # Keep TIN same or fetch from config/session if dynamic

        # Build T108 payload
        query_data = {"invoiceNo": invoice_no}
        content = base64.b64encode(json.dumps(query_data).encode()).decode()

        payload = {
            "data": {
                "content": content,
                "signature": "",
                "dataDescription": {
                    "codeType": "0",
                    "encryptCode": "1",
                    "zipCode": "0"
                }
            },
            "globalInfo": {
                "appId": "AP01",
                "version": "1.1.20191201",
                "dataExchangeId": str(uuid.uuid4()).replace('-', '')[:32],
                "interfaceCode": "T108",
                "requestCode": "TP",
                "requestTime": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "responseCode": "TA",
                "userName": "admin",
                "taxpayerID": "1",
                "deviceMAC": "FFFFFFFFFF",
                "deviceNo": device_no,
                "tin": tin,
                "longitude": "116.397128",
                "latitude": "39.916527",
                "agentType": "0",
                "extendField": {}
            },
            "returnStateInfo": {
                "returnCode": "",
                "returnMessage": ""
            }
        }

        try:
            url = "http://centenary:9880/efristcs/ws/tcsapp/getInformation"
            headers = {'Content-Type': 'application/json'}
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            response_data = response.json()

            return_code = response_data.get("returnStateInfo", {}).get("returnCode", "")
            return_message = response_data.get("returnStateInfo", {}).get("returnMessage", "")
            response_content = response_data.get("data", {}).get("content", "")

            if not response_content:
                return JsonResponse({
                    "status": "error",
                    "message": "EFRIS returned empty content.",
                    "return_code": return_code,
                    "return_message": return_message
                }, status=400)

            decoded_content = base64.b64decode(response_content).decode()
            invoice_data = json.loads(decoded_content)

            return JsonResponse({
                "status": "success",
                "invoice": invoice_data
            })

        except requests.exceptions.RequestException as e:
            return JsonResponse({
                "status": "error",
                "message": f"EFRIS connection failed: {str(e)}"
            }, status=500)

        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": f"Failed to decode or process response: {str(e)}"
            }, status=500)

    return JsonResponse({"status": "error", "message": "Only POST allowed"}, status=405)


# def generate_t108_payload(invoice_no, tin, device_no):
#     """Creates payload for T108: Invoice Detail Query"""
#     query_data = {
#         "invoiceNo": invoice_no
#     }

#     content = base64.b64encode(json.dumps(query_data).encode()).decode()

#     payload = {
#         "data": {
#             "content": content,
#             "signature": "",  # Add signature logic here if required
#             "dataDescription": {
#                 "codeType": "0",
#                 "encryptCode": "1",
#                 "zipCode": "0"
#             }
#         },
#         "globalInfo": {
#             "appId": "AP01",
#             "version": "1.1.20191201",
#             "dataExchangeId": str(uuid.uuid4()).replace('-', '')[:32],
#             "interfaceCode": "T108",
#             "requestCode": "TP",
#             "requestTime": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
#             "responseCode": "TA",
#             "userName": "admin",
#             "taxpayerID": "1",
#             "deviceMAC": "FFFFFFFFFF",
#             "deviceNo": device_no,
#             "tin": tin,
#             "longitude": "116.397128",
#             "latitude": "39.916527",
#             "agentType": "0",
#             "extendField": {}
#         },
#         "returnStateInfo": {
#             "returnCode": "",
#             "returnMessage": ""
#         }
#     }

#     return payload


# @csrf_exempt
# def fetch_invoice_t108(request):
  
#     if request.method == 'POST':
#         invoice_no = request.POST.get('invoiceNo')
#         if not invoice_no:
#             return JsonResponse({"status": "error", "message": "Invoice number is required"}, status=400)

#         tin = "1003118023"
#         device_no = "TCS085e154266969073"

#         payload = generate_t108_payload(invoice_no, tin, device_no)

#         try:
#             url = "http://centenary:9880/efristcs/ws/tcsapp/getInformation"
#             headers = {'Content-Type': 'application/json'}

#             response = requests.post(url, json=payload, headers=headers, timeout=10)
#             response.raise_for_status()

#             response_data = response.json()

#             return_code = response_data.get("returnStateInfo", {}).get("returnCode", "")
#             return_message = response_data.get("returnStateInfo", {}).get("returnMessage", "")
#             response_content = response_data.get("data", {}).get("content", "")

#             # If content is empty, show EFRIS message
#             if not response_content:
#                 return JsonResponse({
#                     "status": "error",
#                     "message": "EFRIS returned empty content.",
#                     "return_code": return_code,
#                     "return_message": return_message
#                 }, status=400)

#             # Try to decode
#             try:
#                 decoded_content = base64.b64decode(response_content).decode()
#                 invoice_data = json.loads(decoded_content)
#             except Exception as decode_err:
#                 return JsonResponse({
#                     "status": "error",
#                     "message": f"Failed to decode content: {str(decode_err)}",
#                     "raw_content": response_content
#                 }, status=500)

#             return JsonResponse({
#                 "status": "success",
#                 "invoice": invoice_data
#             })

#         except requests.exceptions.RequestException as e:
#             return JsonResponse({
#                 "status": "error",
#                 "message": f"EFRIS connection failed: {str(e)}"
#             }, status=500)

#         except Exception as e:
#             return JsonResponse({
#                 "status": "error",
#                 "message": str(e)
#             }, status=500)

#     return JsonResponse({"status": "error", "message": "Only POST allowed"}, status=405)


@csrf_exempt
def upload_invoice_to_efris(request):
    if request.method == 'POST':
        try:
            invoice_data = request.session.get('current_invoice')
            if not invoice_data:
                return JsonResponse({"status": "error", "message": "No invoice data in session"}, status=400)

            # Prepare full payload from invoice_data
            payload = prepare_efris_payload(invoice_data)

            efris_url = "http://centenary:9880/efristcs/ws/tcsapp/getInformation"
            headers = {'Content-Type': 'application/json'}

            response = requests.post(efris_url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()

            response_data = response.json()
            return_code = response_data.get('returnStateInfo', {}).get('returnCode', '')
            return_message = response_data.get('returnStateInfo', {}).get('returnMessage', '')
            response_content = response_data.get('data', {}).get('content', '')

            try:
                decoded_content = base64.b64decode(response_content).decode()
            except Exception:
                decoded_content = response_content

            if return_code == "00":
                return JsonResponse({
                    "status": "success",
                    "response_content": decoded_content,
                    "message": return_message
                })
            else:
                return JsonResponse({
                    "status": "error",
                    "error_code": return_code,
                    "message": return_message
                }, status=400)

        except requests.exceptions.RequestException as e:
            return JsonResponse({
                "status": "error",
                "message": f"Failed to connect to EFRIS API: {str(e)}"
            }, status=500)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Invalid request method. Use POST."}, status=405)


def prepare_efris_payload(invoice_data):
    # Generate a unique Seller's Reference Number each time
    generated_reference_no = "TCS" + str(uuid.uuid4().int)[:16]

    # Update the referenceNo in the invoice data's sellerDetails
    if "sellerDetails" in invoice_data:
        invoice_data["sellerDetails"]["referenceNo"] = generated_reference_no

    # Update invoiceNo if present in basicInformation
    if "basicInformation" in invoice_data:
        invoice_data["basicInformation"]["invoiceNo"] = generated_reference_no

    # Make sure TIN is set or default to empty string
    tin = invoice_data.get("sellerDetails", {}).get("tin", "")

    # Now encode invoice_data to JSON string and base64 encode
    content_str = json.dumps(invoice_data)
    encrypted_content = base64.b64encode(content_str.encode()).decode()

    payload = {
        "data": {
            "content": encrypted_content,
            "signature": "DUMMY_SIGNATURE",  # Adjust if your system requires a real signature
            "dataDescription": {
                "codeType": "1",
                "encryptCode": "1",
                "zipCode": "0"
            }
        },
        "globalInfo": {
            "appId": "AP04",
            "version": "1.1.20191201",
            "dataExchangeId": str(uuid.uuid4()).replace('-', '')[:32],
            "interfaceCode": "T109",
            "requestCode": "TP",
            "requestTime": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "responseCode": "TA",
            "userName": "admin",
            "deviceMAC": "FFFFFFFFFF",
            "deviceNo": "TCS085e15426696907",
            "tin": tin,
            "brn": "",
            "taxpayerID": "1",
            "longitude": "116.397128",
            "latitude": "39.916527",
            "agentType": "0"
        },
        "returnStateInfo": {
            "returnCode": "",
            "returnMessage": ""
        }
    }

    return payload

#ajax to
@csrf_exempt
def save_invoice_session(request):
    if request.method == 'POST':
        try:
            invoice_data = json.loads(request.body)
            request.session['current_invoice'] = invoice_data
            return JsonResponse({"status": "success", "message": "Invoice saved to session"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error", "message": "Only POST allowed"}, status=405)

@csrf_exempt
def download_invoice_pdf(request):
    if request.method == 'POST':
        invoice_json = request.POST.get('invoice_json')
        try:
            invoice_data = json.loads(invoice_json)
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)

        qr_url = invoice_data.get("summary", {}).get("qrCode", "")
        qr_base64 = None
        if qr_url:
            qr = qrcode.make(qr_url)
            buffer = BytesIO()
            qr.save(buffer, format="PNG")
            qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        template_path = 'pdf.html'
        context = {
            'invoice_data': invoice_data,
            'qr_base64': qr_base64
        }

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="invoice.pdf"'

        template = get_template(template_path)
        html = template.render(context)
        pisa_status = pisa.CreatePDF(html, dest=response)
        if pisa_status.err:
            return HttpResponse('Error generating PDF', status=500)
        return response
    return JsonResponse({"status": "error", "message": "Only POST allowed"}, status=405)

def landing(request):
    error = None
    tin_data = None

    if request.method == 'POST':
        tin = request.POST.get('tin')

        try:
            response = requests.post(
                request.build_absolute_uri('/billing-upload/'),
                timeout=10
            )
            result = response.json()

            if result.get('status') == 'success':
                invoice_data = json.loads(result.get('response_content'))

                seller_details = invoice_data.get("sellerDetails", {})
                seller_tin = seller_details.get("tin")

                if seller_tin == tin:
                    # Store tin_data to show in template
                    tin_data = {
                        'legalName': seller_details.get('legalName'),
                        'businessName': seller_details.get('businessName'),
                        'address': seller_details.get('address'),
                        'emailAddress': seller_details.get('emailAddress'),
                        'mobilePhone': seller_details.get('mobilePhone'),
                    }
                    # Save TIN in session so user can proceed to dashboard later
                    request.session['tin'] = seller_tin
                else:
                    error = "TIN not found in uploaded invoice."
            else:
                error = result.get("message", "Failed to fetch invoice data")

        except Exception as e:
            error = f"Error verifying TIN: {str(e)}"

    return render(request, 'landing.html', {
        'error': error,
        'tin_data': tin_data
    })

@csrf_exempt
def dashboard(request):
    if not request.session.get('tin'):
        return redirect('landing')

    invoice_data = None
    error = None

    try:
        response = requests.post(
            request.build_absolute_uri('/billing-upload/'),
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                try:
                    response_content = result.get('response_content')
                    invoice_data = json.loads(response_content) \
                        if isinstance(response_content, str) else response_content
                except json.JSONDecodeError:
                    error = "Invalid invoice data format (JSON decode failed)"
            else:
                error = result.get('message', 'Unknown error occurred')
        else:
            error = f"API error: {response.status_code}"
    except Exception as e:
        error = f"Failed to fetch invoice: {str(e)}"

    return render(request, 'dashboard.html', {
        'invoice_data': invoice_data,
        'error': error,
    })

@csrf_exempt
def generate_receipt(request):
    if request.method == 'POST':
        invoice_json = request.POST.get('invoice_json')
        try:
            invoice_data = json.loads(invoice_json)
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid invoice data"}, status=400)

        return render(request, 'receipt.html', {'invoice': invoice_data})

    return JsonResponse({"status": "error", "message": "Only POST allowed"}, status=405)

def truncate(num, decimals=2):
    factor = 10 ** decimals
    return int(num * factor) / factor

def generate_item_name(base_name, deemed_flag, discount_flag):
    parts = [base_name]
    if deemed_flag == "1":
        parts.append("(Deemed)")
    if discount_flag == "0":
        parts.append("(Discount)")
    return " ".join(parts)

@csrf_exempt
def billing_upload(request):
    if request.method == 'GET':
        return JsonResponse({
            "message": "T109 Upload Endpoint is reachable. Use POST to upload invoice."
        })
    if request.method == 'POST':
        data_exchange_id = str(uuid.uuid4()).replace('-', '')[:32]
        request_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        issued_date = request_time
        generated_reference_no = "TCS" + str(uuid.uuid4().int)[:16]

        base_name = "NC-Black-1Ltr"
        deemed_flag = "2"
        discount_flag = "2"
        item_name = generate_item_name(base_name, deemed_flag, discount_flag)

        qty = 1
        unit_price = 1
        tax_rate = 0.18

        total = truncate(qty * unit_price, 2)
        tax = truncate(total * 18 / 118, 2)
        net_amount = truncate(total - tax, 2)
        gross_amount = total
    
        try:
            # Generate a unique invoice number once per upload
            invoice_no = "INV" + datetime.now().strftime("%Y%m%d%H%M%S")
            device_no = "TCS085e154266969073"  # Use fixed deviceNo everywhere

            # Prepare invoice data
            billing_content = {
                "sellerDetails": {
                    "tin": "1003118023",
                    "referenceNo": invoice_no,
                
                "ninBrn": "1234567890",
                "legalName": "Example Seller Ltd",
                "businessName": "Example Seller Ltd",
                "address": "123 Seller Street, Kampala",
                "mobilePhone": "0772000000",
                "linePhone": "0414000000",
                "emailAddress": "info@flaxem.com",
                "placeOfBusiness": "Kampala",
                    # ... other seller details unchanged ...
                },
                "basicInformation": {
                    "invoiceNo": invoice_no,
                    "deviceNo": device_no,
                    "invoiceType": "1",
                "invoiceKind": "1",
                "invoiceIndustryCode": "101",
                
                "isBatch": "0",
                "operator": "admin",
                "currency": "UGX",
                "issuedDate": issued_date,
               
                "antifakeCode": "12345678901234567890"
                    # ... other basicInformation unchanged ...
                },
                "buyerDetails": {
                "buyerType": "0",
                "buyerTin": "1003118023",
                "buyerNinBrn": "1234567890",
                "buyerLegalName": "Robert Customer",
                "buyerBusinessName": "Robert Customer Ltd",
                "buyerAddress": "456 Buyer Avenue, Kampala",
                "buyerEmail": "buyer@example.com",
                "buyerMobilePhone": "0772000000",
                "buyerLinePhone": "0414000000",
                "buyerPlaceOfBusi": "Kampala",
                "buyerCitizenship": "UG-Uganda"
            },
             "goodsDetails": [
                {
                    "item": item_name,
                    "itemCode": "SL-NC-B0003",
                    "qty": qty,
                    "unitPrice": unit_price,
                    "taxRate": tax_rate,
                    "total": total,
                    "tax": tax,
                    "taxAmount": tax,
                    "netAmount": net_amount,
                    "pack": None,
                    "deemedFlag": deemed_flag,
                    "discountFlag": discount_flag,
                    "commodityCategoryId": "73181104",
                    "goodsCategoryId": "73181104",
                    "orderNumber": 0,
                    "exciseFlag": "2",
                    "unitOfMeasure": "PCE",
                    "categoryId": None,
                    "categoryName": None,
                    "exciseRate": None,
                    "exciseTax": None
                }
            ],
            "taxDetails": [
                {
                    "taxCategory": "Standard",
                    "netAmount": net_amount,
                    "taxRate": tax_rate,
                    "taxAmount": tax,
                    "grossAmount": gross_amount,
                    "taxCategoryCode": "01"
                }
            ],
            "summary": {
                "netAmount": net_amount,
                "taxAmount": tax,
                "grossAmount": gross_amount,
                "itemCount": 1,
                "modeCode": "0",
                "remarks": item_name + " invoice",
                "qrCode": "example.qrcode"
            },
            "payWay": [
                {
                    "paymentMode": "102",
                    "paymentAmount": gross_amount,
                    "orderNumber": "a"
                }
            ],
            "operationType": "101",
            "supplierTin": "1003118023",
            "supplierName": "Example Seller Ltd"
        }
            

            # Build full payload for EFRIS
            content_str = json.dumps(billing_content)
            encrypted_content = base64.b64encode(content_str.encode()).decode()

            payload = {
                "data": {
                    "content": encrypted_content,
                    "signature": "DUMMY_SIGNATURE",
                    "dataDescription": {
                        "codeType": "1",
                        "encryptCode": "1",
                        "zipCode": "0"
                    }
                },
                "globalInfo": {
                    "appId": "AP04",
                    "version": "1.1.20191201",
                    "dataExchangeId": str(uuid.uuid4()).replace('-', '')[:32],
                    "interfaceCode": "T109",
                    "requestCode": "TP",
                    "requestTime": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "responseCode": "TA",
                    "userName": "admin",
                    "deviceMAC": "FFFFFFFFFF",
                    "deviceNo": device_no,
                    "tin": "1003118023",
                    "brn": "",
                    "taxpayerID": "1",
                    "longitude": "116.397128",
                    "latitude": "39.916527",
                    "agentType": "0"
                },
                "returnStateInfo": {
                    "returnCode": "",
                    "returnMessage": ""
                }
            }

            efris_url = "http://centenary:9880/efristcs/ws/tcsapp/getInformation"
            headers = {'Content-Type': 'application/json'}
            response = requests.post(efris_url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()

            response_data = response.json()
            return_code = response_data.get('returnStateInfo', {}).get('returnCode', '')
            return_message = response_data.get('returnStateInfo', {}).get('returnMessage', '')
            response_content = response_data.get('data', {}).get('content', '')

            try:
                decoded_content = base64.b64decode(response_content).decode()
            except Exception:
                decoded_content = response_content

            if return_code == "00":
                # Save invoiceNo and deviceNo in session for fetch
                request.session['last_uploaded_invoice_no'] = invoice_no
                request.session['device_no'] = device_no

                return JsonResponse({
                    "status": "success",
                    "response_content": decoded_content,
                    "message": return_message,
                    "invoiceNo": invoice_no,
                    "deviceNo": device_no
                })
            else:
                return JsonResponse({
                    "status": "error",
                    "error_code": return_code,
                    "message": return_message
                }, status=400)

        except requests.exceptions.RequestException as e:
            return JsonResponse({
                "status": "error",
                "message": f"Failed to connect to EFRIS API: {str(e)}"
            }, status=500)

    return JsonResponse({
        "status": "error",
        "message": "Invalid request method. Use POST."
    }, status=405)
