import requests
import sys

url = "http://localhost:8000/api/ingest"
try:
    files = {'file': open('test_doc.txt', 'rb')}
    print(f"Uploading to {url}...")
    response = requests.post(url, files=files, timeout=60)
    print(f"Status: {response.status_code}")
    print("Response JSON:")
    print(response.json())
except Exception as e:
    print(f"Error: {e}")
