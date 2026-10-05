import requests

def send_mock_webhook():
    url = "http://127.0.0.0:8000/webhook"
    
    # Simulating the JSON data GitHub sends when a test fails
    payload = {
        "repository": "shyam/production-app",
        "error_log": "TypeError: Cannot read properties of undefined (reading 'status') in api_handler.py",
        "pr_number": 42
    }
    
    print(f"🚀 [GitHub Mock] Sending webhook to Autonomous Engine at {url}...")
    try:
        response = requests.post("http://127.0.0.1:8000/webhook", json=payload)
        print(f"📥 [GitHub Mock] Received response from Engine: {response.json()}")
    except requests.exceptions.ConnectionError:
        print("❌ [Error] Could not connect. Is the FastAPI server running?")

if __name__ == "__main__":
    send_mock_webhook()
