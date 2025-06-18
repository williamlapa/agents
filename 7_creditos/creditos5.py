from dotenv import load_dotenv
import os
import requests

# Carrega a API key do arquivo .env
load_dotenv()
api_key = os.getenv("DEEPSEEK_API_KEY")

url = "https://api.deepseek.com/user/balance"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Accept": "application/json"
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    saldo = response.json()
    print("🔹 Saldo disponível:", saldo.get("total_available"))
    print("🔹 Total concedido:", saldo.get("total_granted"))
    print("🔹 Total usado:", saldo.get("total_used"))
else:
    print("❌ Erro:", response.status_code, response.text)
