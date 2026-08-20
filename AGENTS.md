# 프로젝트 작업 지침

## 범위와 목적

- 이 파일은 `/Users/woo/chatbot` 저장소 전체에 적용한다.
- 이 프로젝트는 EBS 중학교 과학 질문·답변 데이터, Mecab 형태소 분석, Gensim Doc2Vec을 결합한 Django 웹 챗봇이다.
- 2021년 Oracle Cloud에서 운영한 레거시 앱을 2026-08-21에 macOS/Python 3.11에서 다시 실행 가능하도록 복구했다.
- 한국어 질문·답변 데이터와 커밋된 원본 Doc2Vec 모델을 보존한다.

## Git과 보존 대상

- 원격은 `https://github.com/drshark95/chatbot.git`, 기본 브랜치는 `master`다.
- 복구 전 기준 커밋은 `5455b8f`이며 전체 과거 이력은 5개 커밋이다.
- 2024-02-16에 이 저장소를 GitHub에서 다시 clone하고 로컬 실행을 시도한 기록이 있다.
- 2024년 작업으로 생긴 기존 `chatbot/` Python 3.10 venv는 인터프리터 연결이 깨졌지만 사용자 기록이므로 삭제하거나 덮어쓰지 않는다. `.gitignore`로만 제외한다.
- 과거 Python 캐시와 `.DS_Store`도 직접 정리하지 않는다. 새 캐시와 로컬 환경은 Git에 추가하지 않는다.
- `git_update.sh`는 `git add .`, commit, push를 연속 수행하므로 사용하지 않는다. 파일을 선별해서 stage한다.
- `db.sqlite3`, 데이터셋, 모델, 과거 로그에는 사용자·질문 데이터가 있을 수 있다. 내용 출력·교체·마이그레이션 전에 민감성을 확인한다.

## 현재 요청 흐름

1. `/`는 `/chat_service/`로 리다이렉트한다.
2. `templates/addresses/chat_service.html`의 same-origin `fetch`가 CSRF 토큰과 질문을 Django에 보낸다.
3. `addresses/views.py`가 질문, user-agent, 요청 IP를 `faq_answer()`에 전달한다.
4. `addresses/faq_chatbot.py`가 `python-mecab-ko`로 품사 토큰을 만들고 Doc2Vec 문서 벡터에서 가장 가까운 질문을 찾는다.
5. 유사도 0.6 이상이면 데이터셋 답변을 반환하고, 미만이면 질문을 구체화하라는 안내를 반환한다.
6. 브라우저는 반환 문자열을 `textContent`로 표시하므로 질문·답변 HTML이 실행되지 않는다.

## 모델과 데이터

- 원본 모델: `model/d2v_faqs_size200_min5_epoch20_ebs_science_qna.model`.
- 파일명과 달리 실제 모델은 vector size 50, 문서 1,213개, Gensim 3.8 계열 구조다.
- 현재 데이터: `data/df2_20210601_edited.xlsx`, 데이터 1,213건, 질문/답변 결측 0건.
- `addresses/legacy_gensim.py`는 원본 파일을 바꾸지 않고 메모리에서 Gensim 3 문서 벡터 필드를 Gensim 4 구조로 승격한다.
- 모델 문서 수와 데이터 행 수가 다르면 앱 시작 시 즉시 `RuntimeError`를 발생시킨다.
- 호환 로더는 Gensim private serialization 구조를 다루므로 Gensim을 올릴 때 모델 로드·추론 테스트를 반드시 먼저 실행한다.

## Python 환경과 의존성

- 현재 검증 환경은 Homebrew Python 3.11.7로 만든 `/Users/woo/chatbot/.venv`다.
- 새 로컬 환경은 `.venv`를 사용하고 기존 `chatbot/` venv는 사용하지 않는다.
- `requirements.txt`는 직접 의존성을, `requirements.lock.txt`는 검증한 전체 환경을 정확한 버전으로 고정한다.
  - Django 5.2.17, DRF 3.18.0, Gensim 4.4.0
  - Pandas 2.3.3, OpenPyXL 3.1.5, PyMySQL 1.2.0
  - python-mecab-ko 1.3.7, Gunicorn 26.1.0
- 환경 생성:
  - `/opt/homebrew/bin/python3 -m venv .venv`
  - `.venv/bin/python -m pip install -r requirements.lock.txt`
- 패키지 설치·업데이트 시 기존 venv를 고치거나 다른 프로젝트 Conda 환경을 빌려 쓰지 않는다.

## 실행과 검증

- 모든 명령은 저장소 루트에서 실행한다.
- 기본 로컬 실행은 외부 DB 기록을 끈다.
  - `CHATBOT_LOG_DB_ENABLED=false .venv/bin/python manage.py check`
  - `CHATBOT_LOG_DB_ENABLED=false .venv/bin/python manage.py test`
  - `CHATBOT_LOG_DB_ENABLED=false .venv/bin/python manage.py runserver 127.0.0.1:8000`
- 검증 완료 항목:
  - `pip check`
  - Django system check
  - `makemigrations --check --dry-run`
  - Gunicorn `--check-config`
  - `collectstatic --noinput --clear`
  - 자동 테스트 7개
  - 실제 브라우저 GET, 질문 POST, 답변 렌더링, 콘솔 오류 없음
- 2026-08-21 브라우저 검증 질문에서 원본 모델이 84%대 유사도로 답변했다.
- 테스트는 외부 MariaDB 연결이 호출되지 않는 것도 mock으로 검증한다.
- 로컬 8000번은 다른 `/Users/woo/django` 프로젝트가 사용할 수 있다. 해당 프로세스를 종료하지 말고 이 프로젝트는 8010 등 빈 포트를 선택한다.

## 로그 DB와 보안

- `CHATBOT_LOG_DB_ENABLED` 기본값은 false이며 이 상태에서는 원격 연결을 전혀 시도하지 않는다.
- MariaDB 로그를 쓸 때만 `CHATBOT_DB_HOST`, `CHATBOT_DB_USER`, `CHATBOT_DB_PASSWORD`, `CHATBOT_DB_NAME`을 환경변수로 제공한다.
- DB 실패는 로그로 남기되 챗봇 답변을 막지 않는다. INSERT는 반드시 매개변수 쿼리를 유지한다.
- 실제 자격 증명은 Git 이력에 노출된 적이 있으므로 재사용하지 말고 회전한다. 문서·로그·응답에 값을 복제하지 않는다.
- Django secret, debug, allowed hosts도 각각 `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS` 환경변수를 사용한다.
- 주소록과 앱 로그인은 레거시 부가 기능이다. 외부 배포 전 CSRF, 인증, rate limit, 개인정보 보존 정책을 별도로 검토한다.

## 과거 및 현재 배포

- 과거 구조는 Oracle Cloud Ubuntu VM의 Nginx → Gunicorn 유닉스 소켓 → Django였다.
- SQLite는 Django 사용자·세션·주소록, 같은 공인 IP의 MariaDB는 질문 로그 용도였다.
- 과거 IP는 Oracle Public Cloud 대역이지만 2026-08-20 80/443 포트가 모두 시간 초과됐다.
- `copy_system_files/`, apt·iptables·systemd 스크립트는 과거 기록이며 현재 macOS에서 실행하지 않는다.
- 루트 `render.yaml`은 Singapore 리전의 무료 Python 웹 서비스 `ebs-science-chatbot`을 정의한다.
- `.python-version`으로 Python 3.11.11을 고정하고 빌드 시 잠금 의존성 설치와 `collectstatic`을 수행한다.
- Gunicorn은 모델 메모리 중복을 막기 위해 worker 1개, thread 4개로 실행하며 `/health/`를 상태 확인에 사용한다.
- Render에서는 `PUBLIC_CHATBOT_ONLY=true`로 챗봇, favicon, health 경로만 등록한다. 레거시 주소록·로그인·관리자·DRF 인증 경로는 공개하지 않는다.
- WhiteNoise가 수집된 정적 파일을 제공하며 외부 MariaDB 질문 기록은 비활성화한다.
- 2026-08-21 생성된 무료 서비스의 공개 주소는 `https://ebs-science-chatbot.onrender.com`이며 Singapore 리전에서 실행된다.
- GitHub `master` 브랜치와 연결되어 커밋 시 자동 배포된다. 무료 인스턴스는 유휴 시 정지하므로 첫 요청이 늦을 수 있다.
- 첫 배포 `51b4838a`에서 Linux 의존성 설치, 정적 파일 수집, Gunicorn 기동, `/health/` 200, 챗봇 실제 질문 응답과 `/admin/` 404를 확인했다.
- 배포 전 `manage.py check --deploy`를 Render와 같은 환경변수로 검증한다.

## 변경 원칙

- 작업 전후 `git status`와 `git diff`로 사용자 변경을 확인한다.
- 대용량 모델·데이터·SQLite·실제 로그를 새로 만들거나 교체할 때는 출처, 행 수, 모델 정합성과 민감성을 기록한다.
- 외부 DB 기록, 서버 재시작, 방화벽 변경, 패키지 설치, Git push는 사용자의 명시적 허가 뒤에만 한다.
- 변경 후에는 최소 system check, 관련 테스트, 실제 화면 또는 HTTP 검증을 수행한다.
- 실행·배포 구조나 지속적으로 유효한 사실이 바뀌면 이 파일과 `README.md`를 함께 갱신한다.
