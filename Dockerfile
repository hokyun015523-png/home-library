FROM python:3.12-slim

# 컨테이너 내부에 존재하는 가상의 작업폴더
WORKDIR /app 

# --- 패키지 설치 ---
# COPY 원본경로 대상경로 --> 로컬의 파일을 컨테이너 안으로 복사
COPY requirements.txt .

# RUN --> 이미지를 만드는 빌드 시점에 한 번 실행되는 명령어
# --no-cache-dir --> pip가 다운로드 캐시를 이미지 안에 남지기 않게 한다.
RUN pip install --no-cache-dir -r requirements.txt

# --- 소스 코드 복사 ---
COPY main.py .
COPY database.py .
COPY models.py .
COPY streamlit_app.py .
COPY services/ ./templates/
COPY templates/ ./templates/
COPY static/ ./static/

# --- 포트 문서와 ---
# EXPOSE --> 컨테이너가 몇 번 포트를 사용할 예정인지 문서로 남기는 명령어
EXPOSE 8000
EXPOSE 8501

# --- 기본 실행 명령 ---
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]