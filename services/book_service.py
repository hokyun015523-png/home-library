'''
home_library_v4 / services/book_service.py
-------------------------------------------
공통 진행되는 로직 구현

기존 JSON API 라우터(/books/lookup, /books/register)
새로 추가되는 HTML 라우터(/ui/books/lookup, /ui/books/register)
조회 -> 중복 확인 -> 등록 (따로 구현되지 않도록 한 파일에 작업)
'''
# dataclass --> "데이터를 담기 위한 클래스"를 아주 짧게 만들어주는 파이썬 표준 도구
#               __init__(생성자)를 쉽게 구현하도록 한다.
#               @dataclass 라고 데코레이터를 넣으면 자동으로 __init__가 생성된다.
from dataclasses import dataclass
from pathlib import Path
import io  # 메모리안에서 파일처럼 다룰 수 있도록 하는 라이브러리
import uuid  # 랜덤 문자열을 생성해주는 라이브러리 (중복되는 파일이 안생기도록 해준다.)
from PIL import Image, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.orm import Session
from models import Book  # models.py에서 정의한 Book클래스 
from services.recognition import lookup_metadata, normalize_isbn

UPLOAD_DIR = Path('uploads')
UPLOAD_DIR.mkdir(exist_ok=True)

@dataclass
class ServiceResult:
    """
    조회/등록 작업의 결과를 표현하는 상자

    API 라우터 --> 실패 시 HTTPException 에러 상태코드로 응답한다.
    HTML 라우터 --> 실패 시 에러 화면이 아니라, "이미 등록된 책입니다"와 같은 안내문구가 나와야 한다.

    status: str --> 결과 상태내는 문자열
        - ok : 정상 등록/조회 성공
        - invalid_isbn : isbn 체크섬이 맞지 않는다(잘못 입력된 isbn)
        - duplicate : 이미 등록된 책
        - not_found : 조회 전용, 국립중앙도서관 api에서 서지정보를 못찾는다.
        - invalid_image : 등록 전용, 업로드한 파일이 이미지가 아니다.
    """
    status: str
    book: Book | None = None
    message: str = ''

def _find_by_isbn(db: Session, isbn: str) -> Book | None:
    """
    내부 전용 헬퍼 함수 (이 파일안에서만 호출해라!)

    반환값
    --------
    Book | None  --> isbn으로 책을 찾았으면 Book 객체, 못 찾았으면 None
    """
    return db.scalar(select(Book).where(Book.isbn == isbn))

def lookup_book_service(isbn: str, db: Session) -> ServiceResult:
    """
    ISBN 만으로 국립중앙도서관 서지정보를 조회해서 책을 등록하는 함수 (main.py의 lookup_book함수를 옮겼다)
    """
    # 1단계: ISBN 형식이 올바른지 체크섬으로 검증
    validated_isbn = normalize_isbn(isbn)
    if not validated_isbn:
        # None을 반환 --> 잘못된 ISBN
        return ServiceResult(status='invalid_isbn', message='유효한 ISBN 형식이 아닙니다.')

    # 2단계: 이미 등록된 책인지 DB에서 확인
    existing_book = _find_by_isbn(db, validated_isbn)
    if existing_book:
        # 참이라면 None아니라 실제 Book객체가 있다는 뜻 --> 이미 있는 책
        return ServiceResult(status='duplicate', book=existing_book, message='이미 등록된 책입니다.')

    # 3단계: 국립중앙도서관 API로 서지정보(제목/저자/출판사) 조회
    metadata = lookup_metadata(validated_isbn)
    if not metadata:
        # API에 존재하지 않는 책이다.
        return ServiceResult(status='not_found', message='조회된 서지정보가 없습니다.')

    # 4단계: Book객체를 만들어서 DB에 저장
    book = Book(
        title=metadata['title'],
        isbn=validated_isbn,
        author=metadata['author'],
        publisher=metadata['publisher'],
        cover_path=None, # 표지 사진 없이 ISBN만으로 등록했기 때문에 이미지경로가 없다.
        recognition_status='confirmed',  # 국립중앙도서관 정식 데이터라서 '확정'으로 표시
    )

    db.add(book) # 이 책을 저장 대기열에 올려라. --> 아직 DB에 실제로 쓰이지는 않았다.
    db.commit()  # 대기열에 있는 책을 DB에 확정 저장해라. --> SQL INSERT 실행
    db.refresh(book)  # DB가 자동 생성한 값 (예: id, created_at)을 book객체에 다시 채워넣는다.
    return ServiceResult(status='ok', book=book)

def register_book_service(isbn: str, raw_image: bytes, original_filename: str, db: Session) -> ServiceResult:
    """
    ISBN + 책 표지 사진을 함께 등록하는 함수 (main.py의 register_book 함수의 로직을 따왔다.)

    1단계, 2단계는 lookup_book_service와 동일한 패턴    
    """
    # 1단계: ISBN 형식이 올바른지 체크섬으로 검증
    validated_isbn = normalize_isbn(isbn)
    if not validated_isbn:
        # None을 반환 --> 잘못된 ISBN
        return ServiceResult(status='invalid_isbn', message='유효한 ISBN 형식이 아닙니다.')

    # 2단계: 이미 등록된 책인지 DB에서 확인
    existing_book = _find_by_isbn(db, validated_isbn)
    if existing_book:
        # 참이라면 None아니라 실제 Book객체가 있다는 뜻 --> 이미 있는 책
        return ServiceResult(status='duplicate', book=existing_book, message='이미 등록된 책입니다.') 

    # 3단계: 업로드된 파일이 진짜 이미지인지 검증
    try:
        with Image.open(io.BytesIO(raw_image)) as probe:
            probe.verify() # 진짜 이미지 파일인지 검사
    except (UnidentifiedImageError, OSError):
        return ServiceResult(status='invalid_image', message='올바른 이미지 파일이 아닙니다.')

    # 4단계: 서버에 실제로 저장할 새 파일명을 만든다.
    extension = Path(original_filename).suffix or '.jpg'   # 이미지 확장자 추출
    filename = f'{uuid.uuid4().hex}{extension}'  # 랜덤하게 파일명 생성

    path = UPLOAD_DIR / filename
    path.write_bytes(raw_image) # 실제로 디스크에 이미지파일을 저장한다.

    # 5단계: 국립중앙도서관에서 서지정보 조회 시도 -> 실패 -> 등록! (책 표지가 있으므로)
    metadata = lookup_metadata(validated_isbn)
    if metadata:
        title = metadata['title']
        author = metadata['author']
        publisher = metadata['publisher']    
        status_value = 'confirmed'
    else:
        # 서지 정보를 못찾았어도 책 표지사진과 ISBN이 있다면 일단 등록한다. 수동 등록
        title = f'수동 등록: ISBN {validated_isbn} (서지정보 조회 실패)'
        author = None
        publisher = None
        status_value = 'needs_review'

    # 6단계: 최종적으로 Book객체를 만들어 DB에 저장
    book = Book(
        title=title,
        isbn=validated_isbn,
        author=author,
        publisher=publisher,
        cover_path=str(path), # DB는 Path객체같은건 모른다. 문자열만 이해한다.
        recognition_status=status_value,
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    return ServiceResult(status='ok', book=book)