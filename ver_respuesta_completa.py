#!/usr/bin/env python
"""
Ver respuesta completa de la tarea
"""
import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

EOSDA_API_KEY = os.getenv('EOSDA_API_KEY')
BASE_URL = "https://api-connect.eos.com"
TASK_ID = "470a38c8-d16a-4b7f-bd5c-0123dbcb78e4"

session = requests.Session()
session.headers.update({
    'x-api-key': EOSDA_API_KEY,
    'Content-Type': 'application/json'
})

url = f"{BASE_URL}/api/gdw/api/{TASK_ID}"
response = session.get(url, timeout=30)

print("="*80)
print(f"RESPUESTA COMPLETA DE LA TAREA")
print("="*80)
print(f"Status Code: {response.status_code}")
print()
print(json.dumps(response.json(), indent=2))
print("="*80)
