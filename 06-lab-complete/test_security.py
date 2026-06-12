import requests
import time

# Cấu hình URL và API Key của bạn trên Railway
BASE_URL = "https://ai-agent-lab-prod-production.up.railway.app"
# Hãy thay bằng key bạn ĐÃ SET TRÊN RAILWAY (ví dụ: your-secret-agent-api-key-here)
API_KEY = "your-secret-agent-api-key-here"

def test_api_key():
    print("1. Testing Authentication (API Key)...")
    # Test 1: Không gửi API Key -> Mong đợi mã lỗi 401
    r1 = requests.post(f"{BASE_URL}/ask", json={"question": "What is Docker?"})
    print(f"   [No Key] Status: {r1.status_code} -> {'✅ Passed (Bị chặn thành công)' if r1.status_code == 401 else '❌ Failed'}")
    
    # Test 2: Gửi API Key hợp lệ -> Mong đợi mã thành công 200
    r2 = requests.post(
        f"{BASE_URL}/ask",
        headers={"X-API-Key": API_KEY},
        json={"question": "What is Docker?"}
    )
    print(f"   [With Key] Status: {r2.status_code} -> {'✅ Passed (Cho phép truy cập)' if r2.status_code == 200 else '❌ Failed'}")

def test_rate_limit():
    print("\n2. Testing Rate Limiting (Gửi liên tục 15 requests)...")
    rate_limited = False
    for i in range(1, 16):
        r = requests.post(
            f"{BASE_URL}/ask",
            headers={"X-API-Key": API_KEY},
            json={"question": f"Spam question {i}"}
        )
        if r.status_code == 429:
            print(f"   Request {i}: Status 429 -> ✅ Passed (Rate limit đã kích hoạt thành công!)")
            rate_limited = True
            break
        else:
            print(f"   Request {i}: Status {r.status_code} (Chưa bị chặn)")
    
if __name__ == "__main__":
    print(f"Testing API Security at: {BASE_URL}\n")
    test_api_key()
    test_rate_limit()
    print("\nHoàn tất bài test mục 04!")