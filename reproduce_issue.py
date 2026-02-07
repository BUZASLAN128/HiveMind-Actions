import httpx
import os

url = "https://api.z.ai/api/coding/paas/v4/"

print(f"Testing connection to {url}")

try:
    with httpx.Client() as client:
        resp = client.get(url)
        print(f"Response: {resp.status_code}")
except Exception as e:
    print(f"Error: {e}")

print("\nTesting with http2=True")
try:
    with httpx.Client(http2=True) as client:
        resp = client.get(url)
        print(f"Response: {resp.status_code}")
except Exception as e:
    print(f"Error: {e}")
