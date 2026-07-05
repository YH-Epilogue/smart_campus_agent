import requests
base = "http://localhost:8000/api/v1"
r = requests.post(f"{base}/auth/login", json={"username":"admin","password":"123456"})
token = r.json()["access_token"]
h = {"Authorization": f"Bearer {token}"}

tests = [
    "我要请假",
    "帮我请假 学号2023001 2024-01-01 到 2024-01-05 因为生病",
    "请假状态 学号2023001",
    "查询学生 学号2023001",
    "请假结束后如何取消",
]
for i, q in enumerate(tests, 1):
    r = requests.post(f"{base}/chat/", json={"session_id":"lt3","query":q}, headers=h)
    ans = r.json()["answer"]
    print(f"[{i}] {q}")
    print(f"    => {ans[:100]}")
    print()
