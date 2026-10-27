import os

# 실제 .env 없이도 테스트가 돌도록, 앱을 불러오기 전에 테스트용 값을 먼저 정한다.
os.environ["SECRET_KEY"] = "test-only-secret-key"
os.environ["CORS_ORIGINS"] = "http://localhost:5173"
