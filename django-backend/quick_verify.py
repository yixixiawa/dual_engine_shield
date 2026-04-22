import os
import json
import django
from django.test import Client

os.environ['DJANGO_SETTINGS_MODULE'] = 'dual_shield_backend.settings'
django.setup()

client = Client()

tests = [
    ("GET", "/api/health/", None),
    ("GET", "/api/schema/", None),
    ("GET", "/api/docs/", None),
    ("GET", "/api/redoc/", None),
    ("POST", "/api/detect/fish/", {"url": "https://example.com"}),
    ("POST", "/api/detect/batch-fish/", {"urls": ["https://example.com"]}),
    ("GET", "/api/detect/fish-config/", None),
    ("POST", "/api/detect/code/", {"code": "print(1)", "language": "python"}),
    ("POST", "/api/detect/batch-code/", {"code_snippets": [{"code": "print(1)", "language": "python"}]}),
    ("POST", "/api/detect/directory/", {"target_dir": "./testing_data", "languages": ["python"]}),
    ("POST", "/api/ipinfo/query/", {"ip_address": "8.8.8.8", "use_cache": True}),
    ("POST", "/api/ipinfo/save/", {"ip_address": "8.8.8.8", "use_cache": True}),
    ("GET", "/api/ipinfo/database-info/", None),
]

fail_count = 0
failures = []

for method, path, data in tests:
    try:
        if method == "GET":
            response = client.get(path, HTTP_HOST='localhost')
        elif method == "POST":
            response = client.post(path, data=json.dumps(data) if data else None, content_type='application/json', HTTP_HOST='localhost')
        
        status = response.status_code
        print(f"{method} {path} {status}")
        
        if status >= 500:
            fail_count += 1
            failures.append(f"{method} {path} {status}")
    except Exception as e:
        status = "EXCEPTION"
        print(f"{method} {path} {status}: {str(e)}")
        fail_count += 1
        failures.append(f"{method} {path} {status}: {str(e)}")

print(f"\nFAIL_COUNT: {fail_count}")
for fail in failures:
    print(fail)
