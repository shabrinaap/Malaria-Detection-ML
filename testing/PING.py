import requests

url = "https://example.com"
try:
    response = requests.get(url, timeout=5)
    if response.status_code == 200:
        print("Website is up.")
    else:
        print("Website returned an error:", response.status_code)
except requests.exceptions.RequestException as e:
    print("Website is down:", e)