'''
home_library_v0 / models.py
-----------------------------
예광탄 방식을 활용한 아주 얇은 코드
스키마, 테이블 만들기 (ORM)
'''
from datetime import datetime
# sqlalchemy의 String --> 최대 길이를 지정해야 한다. 짧고 정해진 범위의 문자열에 적합하다.
#      DB 쪽에서 길이 초과 시 에러가 나서 실수로 너무 긴 값이 들어가는 것을 막아주는 안전장치 역할
# sqlalchemy의 Text --> 길이 제한이 없다. DB가 허용하는 최대치까지
#       리뷰 본문처럼 얼마나 길어질지 예측하기 어려운 긴 글에 적합하다.
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

# ----------------------------
# Book (책) 테이블
# ----------------------------
class Book(Base):
    __tablename__ = 'books'  # 실제로 저장될 DB 테이블 이름 

    id: Mapped[int] = mapped_column(primary_key=True)  # 기본키
    # ISBN은 OCR 인식에 실패하면 아직 모를 수 있으니 None으로 허용
    # String(13) --> 최대 13자까지 저장가능, 현재 ISBN 기준
    # unique=True --> 중복 방지
    # index=True --> 이 컬럼으로 검색할 때 빠르게 찾을 수 있도록 색인 생성
    isbn: Mapped[str | None] = mapped_column(String(13), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(300))
    author: Mapped[str | None] = mapped_column(String(200))
    publisher: Mapped[str | None] = mapped_column(String(200))
    # cover_path --> 업로드 표지 사진의 경로
    # 사진 파일 자체는 DB에 넣지 않고, 파일 시스템에 두고 경로만 기록(일반적인 방식)
    cover_path: Mapped[str | None] = mapped_column(String(500))
    # OCR검증이 성공했는지 실패했는지 상태를 나타내는 문자열
    # default='confirmed' --> 기본값은 'confirmed', confirmed(확정)/needs_review(확인 필요)
    recognition_status: Mapped[str] = mapped_column(String(20), default='confirmed')
    # 이 책이 언제 등록되었는지 자동 기록
    # default=datetime.utcnow --> 저장되는 순간의 시각으로 자동으로 채워준다.
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 관계 설정
    # cascade='all, delete-orphan' --> 책이 삭제되면 그 책에 딸린 독서상태/리뷰도 같이 자동 삭제
    # uselist=False --> 이 책 하나당 독서상태는 딱 하나. 단일 객체, 1:1 관계
    reading: Mapped['ReadingStatus'] = relationship(back_populates='book', 
                                                    cascade='all, delete-orphan',
                                                    uselist=False) 
    review: Mapped['Review'] = relationship(back_populates='book',
                                            cascade='all, delete-orphan',
                                            uselist=False)

# -------------------------------------------
# ReadingStatus (독서 진행 상태) 테이블
# -------------------------------------------    
class ReadingStatus(Base):
    __tablename__ = 'reading_statuses'

    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey('books.id'), unique=True) # 외래키
    current_page: Mapped[int] = mapped_column(Integer, default=0) # 현재 읽은 쪽수, 기본값 0(아직 안 읽음)
    # unread(안읽음) / reading(읽는 중) / done(완독)
    state: Mapped[str] = mapped_column(String(20), default='unread')

    # 관계
    book: Mapped[Book] = relationship(back_populates='reading')

# -------------------------------------------
# Review (리뷰) 테이블
# -------------------------------------------       
class Review(Base):
    __tablename__ = 'reviews'

    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey('books.id'), unique=True) # 외래키
    rating: Mapped[int] = mapped_column(Integer) # 별점 (숫자로 저장)
    content: Mapped[str] = mapped_column(Text) # 리뷰 본문

    # 관계
    book: Mapped[Book] = relationship(back_populates='review')
