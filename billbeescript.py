import os
import requests
import json
from io import BytesIO

BILLBEE_API_KEY = 'YOUR_BILLBEE_API_KEY'
BILLBEE_API_URL = 'https://app.billbee.io/api/v1'
DISCORD_WEBHOOK_URL = 'YOUR_DISCORD_WEBHOOK_URL'
PROVIDER_ID = 'YOUR_PROVIDER_ID'
PRODUCT_ID = 'YOUR_PRODUCT_ID'

def get_new_orders():
    url = f"{BILLBEE_API_URL}/orders?order_state_id=4"
    headers = {"X-Api-Key": BILLBEE_API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data['Data']
    else:
        return []

def create_shipment_with_label(order_id, provider_id, product_id):
    url = f"{BILLBEE_API_URL}/orders/{order_id}/shipments"
    headers = {"X-Api-Key": BILLBEE_API_KEY, "Content-Type": "application/json"}
    payload = {
        "send_mail": False,
        "create_label": True,
        "download_label": False,
        "shipping_provider_id": provider_id,
        "shipping_provider_product_id": product_id
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    if response.status_code == 200:
        data = response.json()
        return data['Data']['ShipmentId']
    else:
        return None

def get_shipment_label(shipment_id):
    url = f"{BILLBEE_API_URL}/shipments/{shipment_id}/label"
    headers = {"X-Api-Key": BILLBEE_API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.content
    else:
        return None

def send_pdf_to_discord(webhook_url, pdf_data, file_name, buyer_name, purchased_items):
    content = f"Käufer: {buyer_name}\nGekaufte Artikel: {', '.join(purchased_items)}"
    payload = {"content": content}
    files = {"file": (file_name, BytesIO(pdf_data), "application/pdf")}
    response = requests.post(webhook_url, data=payload, files=files)
    return response.status_code == 204

# Hauptlogik des Skripts
orders_without_label = get_new_orders()

provider_id = PROVIDER_ID
product_id = PRODUCT_ID

for order in orders_without_label:
    shipment_id = create_shipment_with_label(order['Id'], provider_id, product_id)
    if shipment_id:
        pdf_data = get_shipment_label(shipment_id)
        if pdf_data:
            file_name = f"label_order_{order['Id']}.pdf"
            buyer_name = order['Buyer']['LastName']
            purchased_items = [item['Product']['Title'] for item in order['OrderItems']]
            send_pdf_to_discord(DISCORD_WEBHOOK_URL, pdf_data, file_name, buyer_name, purchased_items)
