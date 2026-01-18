import requests
import json
import sys
import time
import os
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Configurar retry strategy
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("http://", adapter)
http.mount("https://", adapter)

port = os.getenv("PORT", "8000")
url = f"http://localhost:{port}/api/auth/login"
payload = {
    "email": "admin@restauranteelsol.com",
    "password": "admin123"
}
headers = {
    "Content-Type": "application/json"
}

try:
    print(f"Enviando peticion a {url}...")
    # Usar session con retry
    response = http.post(url, json=payload, headers=headers)
    
    print(f"Status Code: {response.status_code}")
    print(f"Respuesta: {response.text}")
    
    if response.status_code == 200:
        print("Login EXITOSO")
    else:
        print("Login FALLIDO")
        
except Exception as e:
    print(f"Error ejecutando test: {e}")
