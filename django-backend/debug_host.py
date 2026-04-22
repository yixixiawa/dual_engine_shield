import os
import django
from django.test import Client

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dual_shield_backend.settings')
django.setup()

client = Client()

def test_request(path, host=None):
    if host:
        print(f"\nRequesting {path} with HTTP_HOST='{host}'")
        response = client.get(path, HTTP_HOST=host)
    else:
        print(f"\nRequesting {path} (default host)")
        response = client.get(path)
    
    status_code = response.status_code
    content = ""
    try:
        content = response.content.decode('utf-8', errors='ignore')[:200]
    except Exception as e:
        content = f"Error decoding: {e}"
        
    print(f"Status Code: {status_code}")
    print(f"Content (first 200 chars): {content}")
    return status_code

status1 = test_request('/api/health/')
status2 = test_request('/api/health/', host='localhost')
status3 = test_request('/api/schema/', host='localhost')
status4 = test_request('/api/docs/', host='localhost')

print("\nConclusion:")
if status1 == 400:
    print("Yes, the 400 error was likely caused by an Invalid HTTP_HOST header (missing or mismatch).")
else:
    print(f"Initial status was {status1}, not 400.")
