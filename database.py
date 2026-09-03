'''
home_library_v3 / database.py
-----------------------------
Docker 결합
    - import os 추가 -> os.getenv() 
    - .env의 환경변수 읽어오기
DB 연결 - postgreSQL

'''
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# os.getenv(변수이름, 기본값)
# - 컨테이너 실행 시 docker-compose.yml의 environment 항목에서 DATABASE_URL이라는 환경변수를
#   넘겨주면 그 값을 사용한다.
#   만약 환경변수가 없으면(=로컬에서 바로 실행할 경우) 기존처럼 사용하기 위해
#   기본값('postgresql+psycopg2://postgres:1234@localhost:5432/home_library_v1')을 
#   넣을 때도 있다. (우리는 생략함---> 생략하면 로컬에서 안돌아간다;;)
# - '로컬 실행'과 '도커 컨테이너 실행' 두 가지 환경을 모두 고려했다. 
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+psycopg2://postgres:1234@localhost:5432/home_library_v1')

engine = create_engine(DATABASE_URL) # SQLAlchemy가 실제와 DB와 통신할 때 사용하는 핵심 객체 
SessionLocal = sessionmaker(bind=engine) # engine에 연결된 세션(대화창)을 만들어주는 팩토리

class Base(DeclarativeBase): # SQLAlchemy 2.0 스타일
    pass

# FastAPI의 Depends(get_db)가 요청마다 이 함수를 호출해서 DB 세션을 하나씩 만들어준다.
# yield 이후의 db.close()는 요청 처리가 끝난 뒤 자동으로 실행되어 연결을 정리한다.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
