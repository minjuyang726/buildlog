# BuildLog 개발 환경 기록

> Phase 0(2026-10-27)에서 확인한 내용입니다. 아직 아무것도 설치하지 않았고, 아래 실행 명령은 **예정**이며 해당 Phase에서 실제로 실행해 보고 확정합니다. Phase 15에서 처음 설치하는 사람용 설명서로 다시 정리합니다.

## 1. 이 컴퓨터에서 확인한 환경

| 도구 | 확인된 버전 |
| --- | --- |
| Windows | 11 Pro |
| Python | 3.13.14 |
| pip | 26.1.2 |
| Node.js | 24.22.1 |
| npm | 11.19.1 |
| Git | 2.55.0 (아직 저장소로 초기화하지 않음) |
| SQLite (Python 내장) | 3.50.4 |

- 개발 서버가 사용할 `8000`번, `5173`번 포트는 비어 있습니다.

## 2. 사용할 패키지의 후보 버전

2026-10-27에 각 저장소(PyPI, npm)에 공개된 최신 버전입니다. **설치 전이므로 서로 호환되는지는 아직 확인하지 않았습니다.** 해당 Phase에서 설치한 뒤 자동 테스트가 통과하는 버전으로 고정합니다.

| 영역 | 패키지 | 최신 버전 | 설치 Phase |
| --- | --- | --- | --- |
| 서버 | fastapi | 0.162.0 | 1 |
| 서버 | uvicorn | 0.54.0 | 1 |
| 서버 | pydantic-settings | 2.16.1 | 1 |
| 서버 | pytest | 9.1.1 | 1 |
| 서버 | httpx | 0.28.1 | 1 |
| 서버 | sqlalchemy | 2.1.6 | 3 |
| 서버 | alembic | 1.20.1 | 3 |
| 서버 | email-validator | 2.3.0 | 4 (이메일 형식 검사에 필요한지 Phase 4에서 확인) |
| 서버 | argon2-cffi | 25.1.0 | 3 (비밀번호 암호화 후보) |
| 서버 | pyjwt | 2.15.1 | 4 (로그인 토큰 후보) |
| 서버 | psycopg | 3.3.6 | 5 |
| 화면 | react, react-dom | 19.3.1 | 2 |
| 화면 | react-router-dom | 7.18.4 | 2 |
| 화면 | vite, @vitejs/plugin-react | 8.3.5, 6.1.2 | 2 |
| 화면 | vitest | 5.0.5 | 2 |
| 화면 | @testing-library/react | 16.3.3 | 2 |
| 화면 | jsdom (화면 테스트용, Phase 2에서 추가) | 30.1.3 | 2 |

- 비밀번호 암호화와 로그인 토큰 패키지는 `plan.md`에서 "Phase 3~4에서 정함"으로 둔 항목이라 위 두 개는 후보일 뿐입니다.

## 3. 주소와 설정

| 항목 | 값 |
| --- | --- |
| 서버 주소 | `http://localhost:8000` |
| 화면 주소 | `http://localhost:5173` |
| 서버 상태 확인 | `GET /api/health` |
| 화면 → 서버 | 화면 개발 서버가 `/api` 요청을 서버로 전달 |
| 개발·테스트 DB 파일 | `database/buildlog.test.sqlite3` (Git 제외) |

### `.env` 항목 이름 (서버, 루트 `.env`)

| 이름 | 설명 | 비밀값 여부 |
| --- | --- | --- |
| `APP_ENV` | 실행 환경 (예: development) | 아니오 |
| `DATABASE_URL` | 데이터베이스 주소. 기본은 SQLite 파일, Phase 5부터 Supabase로 바꿀 수 있음 | **예** (Supabase 주소에는 비밀번호가 들어감) |
| `SECRET_KEY` | 로그인 토큰을 만들 때 쓰는 비밀 키 | **예** |
| `CORS_ORIGINS` | 서버가 요청을 허용할 화면 주소 | 아니오 |

- 화면 환경 변수는 `VITE_`로 시작하면 브라우저에 공개되므로 비밀값을 넣지 않습니다.
- `.env`는 Git에서 제외되고 `.env.example`(이름만 있는 예시)만 기록됩니다. 이미 `.gitignore`에 반영되어 있습니다.

## 4. 실행·테스트 명령 (예정)

Windows PowerShell 기준입니다. 각 Phase에서 실제로 실행해 보고 확정합니다.

| 하는 일 | 명령 | 확인할 Phase |
| --- | --- | --- |
| 서버 가상환경 만들기 | `python -m venv backend\.venv` | 1 |
| 가상환경 켜기 | `backend\.venv\Scripts\Activate.ps1` | 1 |
| 서버 패키지 설치 | `pip install -r backend\requirements.txt` | 1 |
| 서버 실행 | `cd backend` 후 `uvicorn app.main:app --reload --port 8000` | 1 |
| 서버 테스트 | `cd backend` 후 `pytest` | 1 |
| 화면 패키지 설치 | `cd frontend` 후 `npm install` | 2 |
| 화면 실행 | `cd frontend` 후 `npm run dev` | 2 |
| 화면 테스트 | `cd frontend` 후 `npm test` | 2 |
| 테이블 만들기·변경 | `cd backend` 후 `alembic upgrade head` | 3 (실행 확인됨) |
| 새 테이블 변경 이력 만들기 | `cd backend` 후 `alembic revision --autogenerate -m "설명"` | 3 (실행 확인됨) |

## 5. `.gitignore` 보완 예정

현재 `.gitignore`에는 `.env`, `.venv/`, `node_modules/`, `dist/`, `__pycache__/`, `*.log`가 있습니다. 아래는 아직 없어서 Phase 1에서 추가합니다.

- `*.sqlite3` (개발·테스트용 데이터 파일)
- `.pytest_cache/`

## 6. 알아둘 점

- `alembic.ini` 같은 설정 파일에는 한글 주석을 쓰지 않습니다. Windows가 읽지 못해 마이그레이션이 실패합니다.
- 자동 테스트는 `DATABASE_URL`을 임시 SQLite로 바꿔서 실행하므로 `database/buildlog.test.sqlite3`(개발용 데이터)를 건드리지 않습니다.
