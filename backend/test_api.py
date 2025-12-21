import requests
import json

def test_generate_trip():
    url = "http://localhost:8000/api/v1/trip/generate"
    payload = {
        "user_input": "上海两日游"
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print(f"Sending request to {url}...")
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        print(f"Status Code: {response.status_code}")
        try:
            print("Response JSON:")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        except:
            print("Raw Response Content:")
            print(response.text)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    test_generate_trip()
