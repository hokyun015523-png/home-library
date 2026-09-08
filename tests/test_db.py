'''
home_library/tests/test_db.py 
-----------------------------------
GitHub Actions 실습용 최초 테스트 v5 - DB 연동
    - test.yml의 services.postgres가 뛰어준 임시 DB에 실제로 접속해서 Book모델이 저장/조회 되는지 확인
    - DATABASE_URL은 test.yml에서 CI 전용 값으로 주입되므로 이 파일 안에서는 접속 정보가 입력되지 않는다.
    - /books/lookup처럼 국립중앙도서관API를 부르는 부분은 건드리지 않는다.(API키가 CI에 없다)
    - 대신 우리가 직접 통제할 수 있는 DB 저장 부분만 검증한다.
'''
from database import Base, engine, SessionLocal
from models import Book

def test_책을_저장하고_다시_조회할_수_있다():
    # 매 실행마다 완전히 빈 DB이므로 먼저 테이블부터 만들어야 한다.
    Base.metadata.create_all(engine)

    db = SessionLocal()
    
    try:
        book = Book(title='CI 테스트용 책', isbn='9999999999999', author='테스트 저자')
        db.add(book)
        db.commit()
        # DB가 자동으로 채운 id, created_at 등을 다시 읽어온다.
        db.refresh(book)
        
        saved = db.get(Book, book.id)   
        assert saved is not None
        assert saved.titel == 'CI 테스트용 책'

        # models.py에서 default='confirmed'로 정의된 값이 실제로 DB에도 반영되었는지 확인
        assert saved.recognition_status == 'confirmed'

    finally:
        # 테스트는 자기가 만든 데이터를 스스로 치운다는 습관을 들이는 목적
        db.query(Book).delete()
        db.commit()
        db.close()
