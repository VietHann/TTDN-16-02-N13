#!/usr/bin/env python3
"""
Test script để kiểm tra UI chat hoạt động
"""
import json
import requests
import time

BASE_URL = "http://localhost:8069"

def test_chat_ui():
    """Test giao diện chat hoạt động"""
    print("🔧 Test UI Chat hoạt động...")

    try:
        # Test 1: Gửi tin nhắn trống
        print("\n📝 Test 1: Tin nhắn trống")
        response = requests.post(
            f"{BASE_URL}/api/ai/chat",
            headers={
                "X-API-Key": "demo-api-key-12345",
                "Content-Type": "application/json"
            },
            data=json.dumps({
                "message": "",
                "conversation_id": "test_ui_1"
            })
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Result: {data['result']['message']}")

        # Test 2: Gửi tin nhắn bình thường
        print("\n📝 Test 2: Tin nhắn bình thường")
        response = requests.post(
            f"{BASE_URL}/api/ai/chat",
            headers={
                "X-API-Key": "demo-api-key-12345",
                "Content-Type": "application/json"
            },
            data=json.dumps({
                "message": "Xin chào, đây là test UI",
                "conversation_id": "test_ui_2"
            })
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            success = data['result']['success']
            print(f"Success: {success}")
            if success:
                print("✅ Chat hoạt động tốt!")

        # Test 3: Xóa lịch sử
        print("\n🗑️ Test 3: Xóa lịch sử")
        response = requests.post(
            f"{BASE_URL}/api/ai/clear",
            headers={
                "X-API-Key": "demo-api-key-12345",
                "Content-Type": "application/json"
            },
            data=json.dumps({
                "conversation_id": "test_ui_2"
            })
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Cleared count: {data['result']['data']['deleted_count']}")
            print("✅ Xóa lịch sử hoạt động!")

        print("\n🎉 TẤT CẢ TEST HOÀN THÀNH!")

    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    test_chat_ui()