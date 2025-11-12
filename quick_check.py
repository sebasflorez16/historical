#!/usr/bin/env python
import os, requests, json
from dotenv import load_dotenv
load_dotenv()

TASK_ID = "d2d84848-c6ae-420f-a680-736e7165e8d3"  # Última tarea
session = requests.Session()
session.headers.update({'x-api-key': os.getenv('EOSDA_API_KEY'), 'Content-Type': 'application/json'})

response = session.get(f"https://api-connect.eos.com/api/gdw/api/{TASK_ID}", timeout=30)
print(json.dumps(response.json(), indent=2))
