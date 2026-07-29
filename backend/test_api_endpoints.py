import json
import urllib.request

BASE_URL = "http://127.0.0.1:5000/api"

def make_request(url, method="GET", data=None):
    headers = {"Content-Type": "application/json"}
    req_data = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = json.loads(e.read().decode("utf-8"))
        return e.code, body

def run_tests():
    print("=== 🚀 Running API Endpoints Verification Suite ===")

    # 1. Health check
    status, res = make_request(f"{BASE_URL}/health")
    assert status == 200 and res["success"] is True, f"Health failed: {res}"
    assert "data" in res and "message" in res
    print("✅ 1. GET /api/health passed:", res["message"])

    # 2. Analyze video
    sample_url = "https://www.youtube.com/watch?v=aircAruvnKk"
    status, res = make_request(f"{BASE_URL}/analyze", method="POST", data={"url": sample_url})
    assert status == 200 and res["success"] is True, f"Analyze failed: {res}"
    assert "data" in res and res["data"]["has_transcript"] is True
    video_id = res["data"]["video_id"]
    print("✅ 2. POST /api/analyze passed:", video_id, res["data"]["metadata"]["title"])

    # 3. Summary generation
    status, res = make_request(f"{BASE_URL}/summary", method="POST", data={"video_id": video_id, "style": "quick"})
    assert status == 200 and res["success"] is True, f"Summary failed: {res}"
    assert "content" in res["data"]
    print("✅ 3. POST /api/summary passed. Content length:", len(res["data"]["content"]))

    # 4. Grounded Chat
    status, res = make_request(f"{BASE_URL}/chat", method="POST", data={"video_id": video_id, "question": "What is neural network?"})
    assert status == 200 and res["success"] is True, f"Chat failed: {res}"
    assert "answer" in res["data"]
    print("✅ 4. POST /api/chat passed. Answer snippet:", res["data"]["answer"][:80])

    # 5. Asset Generation
    status, res = make_request(f"{BASE_URL}/generate", method="POST", data={"video_id": video_id, "asset_type": "flashcards"})
    assert status == 200 and res["success"] is True, f"Generate failed: {res}"
    print("✅ 5. POST /api/generate passed.")

    # 6. Missing transcript / invalid video id chat error test
    status, res = make_request(f"{BASE_URL}/chat", method="POST", data={"video_id": "nonexistent_123", "question": "Hi"})
    assert status == 404 and res["success"] is False, f"Expected 404, got {status}: {res}"
    assert res["error"] == "No transcript available for this video."
    print("✅ 6. Grounded Chat error handling passed:", res["error"])

    # 7. History test
    status, res = make_request(f"{BASE_URL}/history")
    assert status == 200 and res["success"] is True, f"History failed: {res}"
    print("✅ 7. GET /api/history passed. Total items:", len(res["data"]["history"]))

    print("\n🎉 ALL API CONTRACT & INTEGRATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
