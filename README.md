# 중학교 과학 질문·답변 챗봇

EBS 중학교 과학 질문·답변 데이터와 Mecab, Doc2Vec을 사용하는 Django 웹 챗봇입니다. 2021년 Oracle Cloud에서 운영하던 프로젝트를 현재 macOS와 Python 3.11 환경에서 다시 실행할 수 있도록 복구했습니다.

## 구성

- Django가 채팅 화면과 HTTP 요청을 처리합니다.
- `python-mecab-ko`가 질문을 형태소와 품사로 분석합니다.
- 커밋된 Gensim 3 Doc2Vec 모델을 호환 로더가 Gensim 4 런타임으로 읽습니다.
- 질문 1,213건이 들어 있는 `data/df2_20210601_edited.xlsx`에서 가장 유사한 질문과 답변을 찾습니다.
- 과거 원격 MariaDB 로그 기록은 기본적으로 꺼져 있어 로컬 실행 중 외부 서버에 접속하지 않습니다.

## 로컬 실행

Python 3.11이 필요합니다. 저장소 루트에서 다음을 실행합니다.

```bash
/opt/homebrew/bin/python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
CHATBOT_LOG_DB_ENABLED=false .venv/bin/python manage.py check
CHATBOT_LOG_DB_ENABLED=false .venv/bin/python manage.py runserver 127.0.0.1:8000
```

브라우저에서 <http://127.0.0.1:8000/>을 열면 `/chat_service/`로 이동합니다.
`requirements.txt`는 직접 의존성 목록이고 `requirements.lock.txt`는 검증한 전체 환경을 고정합니다.

## 검증

```bash
CHATBOT_LOG_DB_ENABLED=false .venv/bin/python manage.py test
```

테스트는 모델·데이터 개수, Mecab 품사 필터, 외부 DB 비접속, Django 화면과 질문 POST를 확인합니다.

## 선택적 MariaDB 로그

질문 기록이 꼭 필요할 때만 아래 환경변수를 별도로 설정합니다. 자격 증명을 Git에 커밋하지 마세요.

```bash
export CHATBOT_LOG_DB_ENABLED=true
export CHATBOT_DB_HOST=127.0.0.1
export CHATBOT_DB_USER=chatbot
export CHATBOT_DB_PASSWORD='replace-me'
export CHATBOT_DB_NAME=chatbot_datalog
```

DB가 꺼져 있거나 연결에 실패해도 챗봇 답변은 계속 반환됩니다.

## 과거 배포 구조

과거에는 Oracle Cloud Ubuntu VM에서 Nginx가 80번 포트 요청을 받고, systemd로 실행한 Gunicorn의 유닉스 소켓에 전달했습니다. Django 사용자·세션은 SQLite에, 챗봇 질문 로그는 같은 공인 IP의 MariaDB에 저장했습니다. `copy_system_files/`와 서버 설치 스크립트는 당시 기록으로 남겨 둔 것이며 현재 macOS 로컬 실행에는 필요하지 않습니다.

## 출처

초기 구현은 <https://cholol.tistory.com/478>의 Doc2Vec·Mecab·Django 예제를 참고했고, 질문·답변 데이터는 EBS 중학교 과학 자료를 기반으로 합니다.
