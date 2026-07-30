#!/usr/bin/env python3
"""
Test chat interface with multiple messages.
Run with: python3 test_chat.py
"""
import sys
import time
import requests

BASE_URL = "http://localhost:8000"

TEST_MESSAGES = [
    ("你好", "简单问候"),
    ("我是谁？", "身份确认"),
    ("曹操 在吗？", "人物查询"),
    ("你是谁？", "AI身份")
]

def test_chat(message, description):
    """Send a chat message and return the response."""
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json={"message": message},
            params={"ouid": "shu"},
            timeout=35
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "success",
                "response": data.get("response", ""),
                "ouid": data.get("ouid", "")
            }
        elif response.status_code == 500:
            return {
                "status": "error_500",
                "message": response.json().get("detail", "Unknown error")
            }
        else:
            return {
                "status": "error",
                "status_code": response.status_code,
                "message": response.text
            }
    except requests.Timeout:
        return {"status": "timeout"}
    except requests.RequestException as e:
        return {"status": "request_error", "error": str(e)}

def main():
    print("=" * 60)
    print("CHAT INTERFACE TEST")
    print("=" * 60)
    
    # Check if server is running
    try:
        health = requests.get(f"{BASE_URL}/health", timeout=5)
        if health.status_code != 200:
            print("ERROR: Server not responding!")
            return 1
    except requests.RequestException as e:
        print(f"ERROR: Cannot connect to server: {e}")
        return 1
    
    print("Server is running. Testing messages:\n")
    
    results = []
    for i, (msg, desc) in enumerate(TEST_MESSAGES, 1):
        print(f"[{i}/{len(TEST_MESSAGES)}] Testing: '{msg}' ({desc})")
        
        result = test_chat(msg, desc)
        results.append((msg, desc, result))
        
        if result["status"] == "success":
            print(f"    ✓ Response: {result['response'][:100]}...")
        elif result["status"] == "error_500":
            print(f"    ✗ 500 Error: {result['message']}")
        else:
            print(f"    ✗ {result['status']}: {result.get('error', result.get('message', ''))}")
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    success_count = sum(1 for _, _, r in results if r.get("status") == "success")
    error_count = len(results) - success_count
    
    print(f"Total messages: {len(TEST_MESSAGES)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {error_count}")
    
    if error_count > 0:
        print("\nFailed messages:")
        for msg, desc, result in results:
            if result.get("status") != "success":
                print(f"  - '{msg}' ({desc}): {result.get('status')}")
    
    return 0 if error_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
