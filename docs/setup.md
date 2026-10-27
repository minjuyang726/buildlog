# BuildLog 설치와 실행 방법

처음 이 프로젝트를 받은 사람이 이 문서만 보고 BuildLog를 실행하고 시험해 볼 수 있도록 정리했습니다.
명령은 **Windows PowerShell** 기준입니다.

## 1. 준비물

| 도구 | 개발할 때 사용한 버전 |
| --- | --- |
| Python | 3.13 |
| Node.js (npm 포함) | 24 |
| Git | 2.5 이상 |

## 2. 처음 한 번만 하는 설치

프로젝트 폴더(`buildlog`) 안에서 진행합니다.

### 2-1. 설정 파일 만들기

```powershell
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

두 번째 명령이 출력한 긴 글자를 복사해서, `.env` 파일의 `SECRET_KEY=` 뒤에 붙여넣습니다.

- `.env`에는 비밀값이 들어가므로 **Git에 올라가지 않습니다.** 다른 사람에게 보내거나 채팅에 붙여넣지 마세요.
- `SECRET_KEY`가 비어 있으면 서버가 시작되지 않습니다.

### 2-2. 서버 설치

```powershell
python -m venv backend\.venv
backend\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
cd backend
alembic upgrade head
cd ..
```

- `alembic upgrade head`는 데이터베이스 파일(`database/buildlog.test.sqlite3`)을 만들고 필요한 표(테이블)를 모두 만듭니다.
- PowerShell에서 스크립트 실행이 막혀 있다면 `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`를 한 번 실행한 뒤 다시 시도합니다.

### 2-3. 화면 설치

```powershell
cd frontend
npm install
cd ..
```

## 3. 실행하기

터미널을 **두 개** 엽니다.

**터미널 1 — 서버**

```powershell
backend\.venv\Scripts\Activate.ps1
cd backend
uvicorn app.main:app --reload --port 8000
```

**터미널 2 — 화면**

```powershell
cd frontend
npm run dev
```

브라우저에서 <http://localhost:5173> 을 엽니다. 처음에는 회원가입부터 하면 됩니다.

- 서버가 켜져 있는지 확인: <http://localhost:8000/api/health> 에서 `{"status":"ok"}`가 보이면 정상입니다.
- 서버의 자동 설명 문서: <http://localhost:8000/docs> (개발 환경에서만 열립니다)
- 끌 때는 각 터미널에서 `Ctrl + C`를 누릅니다. 껐다 켜도 저장한 기록은 남아 있습니다.

## 4. 시험(테스트) 실행

```powershell
# 서버 (가상환경을 켠 상태에서)
cd backend
pytest

# 화면
cd frontend
npm test
npm run lint
npm run build
```

- 자동 테스트는 임시 데이터베이스를 따로 만들어 쓰므로, 내 기록(`database/buildlog.test.sqlite3`)을 건드리지 않습니다.
- 2026-10-27 기준 결과: 서버 396개, 화면 108개 모두 통과했습니다.

## 5. 설정 항목 (`.env`)

| 이름 | 설명 | 기본값 | 비밀값 |
| --- | --- | --- | --- |
| `APP_ENV` | 실행 환경. `development`가 아니면 자동 문서(`/docs`)가 닫히고 로그인 쿠키에 `Secure`가 붙습니다 | `development` | 아니오 |
| `DATABASE_URL` | 데이터베이스 주소 | `sqlite:///database/buildlog.test.sqlite3` | **예** (Supabase 주소에는 비밀번호가 들어갑니다) |
| `SECRET_KEY` | 로그인 상태를 증명하는 데 쓰는 비밀 키. 반드시 직접 만들어 넣어야 합니다 | 없음 | **예** |
| `CORS_ORIGINS` | 서버가 요청을 받아 줄 화면 주소. 여러 개면 쉼표로 구분 | `http://localhost:5173` | 아니오 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | (선택) 로그인 상태를 유지하는 시간(분) | `10080` (7일) | 아니오 |

- 화면 쪽 환경 변수 중 `VITE_`로 시작하는 값은 브라우저에 그대로 공개됩니다. 비밀값을 넣지 마세요.
- 비밀 키를 바꾸면 모든 사용자가 로그아웃되고 다시 로그인해야 합니다.

## 6. 데이터 관리

| 하고 싶은 일 | 방법 |
| --- | --- |
| 기록이 어디에 저장되나요? | `database/buildlog.test.sqlite3` 파일 하나에 모두 저장됩니다 (Git에는 올라가지 않음) |
| 백업 | 서버를 끈 뒤 위 파일을 복사해 둡니다 |
| 처음부터 다시 시작 | 서버를 끄고 위 파일을 지운 뒤 `cd backend` → `alembic upgrade head` |
| 표 구조가 바뀐 새 버전을 받았을 때 | `cd backend` → `alembic upgrade head` |

## 7. 운영자가 신고를 확인하는 방법

BuildLog에는 신고 내용을 보여주는 화면이나 서버 요청이 **일부러 없습니다.** 신고 내용은 일반 사용자에게 보이면 안 되기 때문입니다.
운영자는 데이터베이스에서 직접 `reports` 표를 봅니다.

| 열 | 뜻 |
| --- | --- |
| `reporter_id` | 신고한 사용자 번호 (`users` 표의 `id`) |
| `study_id` / `todo_id` / `error_id` / `comment_id` | 신고 대상. 넷 중 정확히 하나만 값이 있습니다 |
| `reason` | 신고 이유 |
| `created_at` | 신고한 시각 (UTC) |

- 지금(SQLite) 환경에서는 SQLite를 열 수 있는 도구(예: DB Browser for SQLite)로 `database/buildlog.test.sqlite3`의 `reports` 표를 엽니다.
- Supabase를 쓰게 되면 Supabase 화면의 Table Editor에서 `reports` 표를 엽니다.
- 신고만으로 기록이나 댓글이 자동으로 지워지거나 숨겨지지 않습니다. 필요하면 운영자가 판단해서 처리합니다.
- 신고 대상 기록이 삭제되면 그 신고도 함께 삭제됩니다.

## 8. Supabase 사용하기 (아직 실제 연결은 확인하지 못했습니다)

> **현재 상태: 미완료.** Supabase 프로젝트의 접속 정보가 없어서 Phase 5(Supabase 연결 확인)를 진행하지 못했습니다.
> 지금까지의 모든 기능은 SQLite로만 실제 확인했습니다. 아래 절차는 준비된 부분과 앞으로 확인해야 할 부분을 정리한 것입니다.

준비된 것

- 모든 표를 만드는 마이그레이션에 **Supabase 외부 접근 차단 설정**(Row Level Security 켜기)이 들어 있습니다. SQLite에서는 아무 일도 하지 않고, PostgreSQL에서만 실행됩니다.
- 불리언 기본값 등 SQLite와 PostgreSQL이 다르게 동작하는 부분은 두 곳에서 모두 맞도록 작성했습니다.

앞으로 해야 할 일 (사용자가 직접)

1. Supabase 프로젝트를 만듭니다.
2. 데이터베이스 접속 주소를 `.env`의 `DATABASE_URL`에 **직접** 입력합니다. (채팅이나 Git에 올리지 마세요)
3. PostgreSQL 연결 패키지(`psycopg`)를 설치하고 `requirements.txt`에 반영합니다.
4. `alembic upgrade head`를 실행해 표를 만듭니다.
5. 아래를 확인합니다.
   - Supabase 화면에서 모든 표에 Row Level Security가 켜져 있는지
   - Supabase의 공개 키로는 표를 읽을 수 없는지
   - 회원가입·로그인·기록 쓰기가 Supabase에서도 똑같이 되는지
6. 실제 서비스 주소에서 쓸 때는 `APP_ENV=production`으로 바꾸고, 반드시 **HTTPS**로 접속하게 합니다. (로그인 쿠키에 `Secure`가 붙어서 HTTPS가 아니면 로그인되지 않습니다.)

## 9. 알아둘 점 (첫 버전의 한계)

- **목록에 쪽 나누기가 없습니다.** 기록이 아주 많아지면 목록이 느려질 수 있습니다.
- **로그인 시도 횟수 제한이 없습니다.** 인터넷에 공개하기 전에 필요 여부를 정해야 합니다.
- **이메일 확인, 비밀번호 찾기가 없습니다.** 비밀번호를 잊으면 직접 복구할 방법이 없습니다. (첫 버전에서 제외하기로 한 기능입니다)
- 이메일은 소문자로 저장해 대소문자를 구분하지 않고, 닉네임은 정확히 같은 글자만 중복으로 봅니다. (`PRD.md` T4 기본안)
- 기록을 비공개로 바꾸면 댓글과 좋아요는 지워지지 않고 숨겨지며, 이때는 작성자에게도 보이지 않습니다. 다시 공개하면 그대로 돌아옵니다.
- 공개 기록 화면에는 **내가 공개한 기록도 함께** 보입니다. `(나)`로 표시됩니다.
- 설정 파일(`alembic.ini` 등)에는 한글 주석을 쓰지 마세요. Windows가 읽지 못해 마이그레이션이 실패합니다.
- 화면은 Chrome에서 폭 360px(휴대폰)과 1280px(컴퓨터)로 확인했습니다. **Edge와 Safari는 직접 확인하지 못했습니다.**

## 10. 문제가 생겼을 때

| 증상 | 원인과 해결 |
| --- | --- |
| 서버가 시작되지 않고 `secret_key Field required` 같은 문구가 나옴 | `.env`가 없거나 `SECRET_KEY`가 비어 있습니다. 2-1을 다시 합니다 |
| 화면에 "서버에 연결하지 못했습니다"가 보임 | 서버(터미널 1)가 꺼져 있습니다. 3번대로 서버를 켭니다 |
| `Address already in use` / 포트 사용 중 | 8000번(서버) 또는 5173번(화면)을 다른 프로그램이 쓰고 있습니다. 이전 터미널을 `Ctrl + C`로 끄거나 해당 프로그램을 종료합니다 |
| 로그인이 갑자기 풀림 | `SECRET_KEY`를 바꿨거나 7일이 지났습니다. 다시 로그인합니다 |
| `alembic upgrade head`에서 `UnicodeDecodeError` | `alembic.ini`에 한글이 들어갔습니다. 영어로 바꿉니다 |
| `no such table` 오류 | 표를 아직 만들지 않았습니다. `cd backend` → `alembic upgrade head` |

## 11. 폴더 구조

```text
buildlog/
├─ backend/                 # FastAPI 서버
│  ├─ app/
│  │  ├─ main.py            # 서버 시작점 (create_app)
│  │  ├─ core/              # 설정(.env), 비밀번호·로그인 처리, 오류 안내 문구
│  │  ├─ db/                # 데이터베이스 연결, Supabase 접근 차단 도구
│  │  ├─ models/            # 저장되는 데이터 (사용자, 공부 기록, 할 일, 오류 기록, 댓글, 좋아요, 신고)
│  │  ├─ schemas/           # 입력 검사와 응답 모양
│  │  ├─ routers/           # 기능별 요청 처리
│  │  └─ services/          # 로그인 확인, 공개·비공개 권한 검사
│  ├─ alembic/              # 표 구조 변경 이력
│  └─ tests/                # 서버 자동 테스트
├─ frontend/                # React 화면
│  └─ src/
│     ├─ api/               # 서버 요청 모음
│     ├─ components/        # 공통 부품 (양식, 확인창, 댓글, 좋아요, 신고 …)
│     ├─ context/           # 로그인한 사용자 정보
│     ├─ pages/             # 화면
│     └─ styles/            # CSS
├─ database/                # 개발용 SQLite 파일 (Git 제외)
└─ docs/                    # 요구사항(PRD), 동작 설명서(spec), 개발 계획(plan), 이 문서
```

## 12. 문서 안내

| 문서 | 내용 |
| --- | --- |
| [mvp.md](mvp.md) | 처음 정한 MVP 범위 |
| [PRD.md](PRD.md) | 무엇을 만들지 정리한 제작 주문서 |
| [spec.md](spec.md) | 기능별 동작 설명서 |
| [plan.md](plan.md) | 개발 순서와 진행 상황 |
| setup.md | 이 문서 (설치, 실행, 운영 방법) |
