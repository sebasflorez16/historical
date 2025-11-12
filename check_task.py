#!/usr/bin/env python
import os, requests, json, time
from dotenv import load_dotenv
load_dotenv()

TASK_ID = "35807475-7bbc-4b13-8aba-b059e36c9bdf"  # Múltiples índices mayúsculas
session = requests.Session()
session.headers.update({'x-api-key': os.getenv('EOSDA_API_KEY'), 'Content-Type': 'application/json'})
url = f"https://api-connect.eos.com/api/gdw/api/{TASK_ID}"

print(f"Consultando tarea {TASK_ID}...\n")

for i in range(20):
    response = session.get(url, timeout=30)
    data = response.json()
    
    task_type = data.get('task_type', 'unknown')
    status = data.get('status', 'unknown')
    
    print(f"Intento {i+1}: task_type={task_type}, status={status}")
    
    if task_type == 'error':
        print(f"\n❌ ERROR:")
        print(json.dumps(data.get('error_message', {}), indent=2))
        break
    
    if 'result' in data and data['result']:
        print(f"\n✅ RESULTADOS!")
        print(f"Total escenas: {len(data['result'])}")
        if len(data['result']) > 0:
            print(f"\nPrimera escena:")
            print(json.dumps(data['result'][0], indent=2)[:500])
        break
    
    if i < 19:
        time.sleep(10)

print("\n" + "="*80)
