import requests
import json
from config import CRYPTO_TOKEN

class CryptoPayAPI:
    def __init__(self, token):
        self.token = token
        self.base_url = "https://pay.crypt.bot/api"
        self.headers = {
            "Crypto-Pay-API-Token": self.token,
            "Content-Type": "application/json"
        }
    
    def create_invoice(self, amount, payload=""):
        url = f"{self.base_url}/createInvoice"
        data = {
            "asset": "USDT",
            "amount": str(amount),
            "description": "Пополнение баланса в боте",
            "payload": payload,
            "allow_comments": False,
            "allow_anonymous": False
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=data)
            if response.status_code == 200:
                return response.json().get("result")
            return None
        except Exception as e:
            print(f"Error creating invoice: {e}")
            return None
    
    def check_invoice(self, invoice_id):
        url = f"{self.base_url}/getInvoices?invoice_ids={invoice_id}"
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                invoices = response.json().get("result", {}).get("items", [])
                return invoices[0] if invoices else None
            return None
        except Exception as e:
            print(f"Error checking invoice: {e}")
            return None