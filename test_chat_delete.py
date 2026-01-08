#!/usr/bin/env python3
"""
Test script để debug lỗi xóa chat history
"""

import json
import requests

# Test API endpoints
BASE_URL = "http://localhost:8069"

def test_clear_chat():
    """Test xóa lịch sử chat"""
    try:
        print("🔧 Test xóa lịch sử chat...")

        # Test clear API
        response = requests.post(
            f"{BASE_URL}/api/ai/clear",
            headers={
                "X-API-Key": "demo-api-key-12345",
                "Content-Type": "application/json"
            },
            data=json.dumps({
                "conversation_id": "default"
            })
        )

        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text}")

        if response.status_code == 200:
            data = response.json()
            print("✅ API call successful")
            print(f"Result: {data}")
        else:
            print(f"❌ API call failed with status {response.status_code}")

    except Exception as e:
        print(f"❌ Error: {e}")

def test_create_chat_record():
    """Test tạo record chat history với message rỗng"""
    try:
        print("\n🔧 Test tạo record chat với message rỗng...")

        # Test create record with empty message - should fail
        response = requests.post(
            f"{BASE_URL}/api/ai/chat",
            headers={
                "X-API-Key": "demo-api-key-12345",
                "Content-Type": "application/json"
            },
            data=json.dumps({
                "message": "",  # Empty message
                "conversation_id": "test_empty"
            })
        )

        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_clear_chat()
    test_create_chat_record()