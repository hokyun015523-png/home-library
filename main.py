'''
home_library_v4 / main.py
-----------------------------
기존 JSON API 라우터(/books/lookup, /books/register, /books) 응답형태 그대로 두고,
새로 추가되는 HTML 라우터(/ui/books/lookup, /ui/books/register, /shelf)를 추가
'''
from pathlib import Path
from fastapi import Depends, FastAPI, File, Form, UploadFile, status, HTTPException, Request

# StaticFiles --> 해당 폴더 안의 파일들을 그대로 웹 주소로 접근 가능하게 공개하는 기능
from fastapi.staticfiles import StaticFiles

# Jinja2Templates --> templates 폴더 안의 .html파일에 파이썬 데이터를 채워서 완성된 HTML 페이지로 만들어준다.
from fastapi.templating import Jinja2Templates

from sqlalchemy import select
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import Book

# services폴더 안 book_service.py의 lookup_book_service, register_book_service 가져와라!
from services.book_service import lookup_book_service, register_book_service

UPLOAD_DIR = Path('uploads')
UPLOAD_DIR.mkdir(exist_ok=True)

Base.metadata.create_all(engine)

app = FastAPI(title='우리집 책장 API version.4')

# ------------------------------------------------------------------------------
# 정적 파일(이미지, CSS) 공개 설정

# app.mount(주소, 무엇을, 이름)
#   - uploads 폴더 (책 표지)
#   - static 폴더 (css)
# 
# 주소를 직접 문자열로 '/static/style.css'라고 하드코딩하지 않는 이유
#   - 나중에 마운트 경로가 바뀌어도 템플릿을 일일이 안 고쳐도 되게 하기 위해.
# ------------------------------------------------------------------------------
app.mount('/uploads', StaticFiles(directory=UPLOAD_DIR), name='uploads')
app.mount('/static', StaticFiles(directory='static'), name='static')

templates = Jinja2Templates(directory='templates') # html찾아라!



def _duplicate_detail(existing_book: Book) -> dict:
    """
    중복된 책을 만났을 때 응답에 실을 정보를 한 곳에서 만든다.
    lookup_book, register_book 두 군데에서 똑같이 재사용하기 위한 헬퍼 함수
    """
    return {
        'message': '이미 등록된 책입니다.',
        'existing_book': {
            'id': existing_book.id,
            'title': existing_book.title,
            'author': existing_book.author,
            'publisher': existing_book.publisher,
            'recognition_status': existing_book.recognition_status,
        },
    }

# 기존 API 라우터--------------------------------------------------
@app.get('/books/lookup')
def lookup_book(isbn: str, db: Session = Depends(get_db)):
    """isbn이 들어오면 DB에서 찾아서 결과 확인"""
    result = lookup_book_service(isbn, db)

    if result.status == 'invalid_isbn':
        # 상태 코드 422 --> Unporcessable Entity (요청은 이해했지만 값이 유효하지 않다)
        raise HTTPException(422, re .message)
    if result.status == 'duplicate':
        # 상태코드 409 --> Conflict (이미 존재하는 것과 충돌, 여기서는 이미 등록된 책)
        raise HTTPException(status.HTTP_409_CONFLICT, _duplicate_detail(result.book))
    if result.status == 'not_found':
        # 상태코드 404 --> Not Found (요청한대상을 찾을 수 없다. 서지 정보 없다.)
        raise HTTPException(404, result.message)

    return result.book


@app.post('/books/register', status_code=status.HTTP_201_CREATED)
def register_book(isbn: str=Form(...), image: UploadFile=File(...), db: Session=Depends(get_db)):
    """isbn, 책 표지를 DB에 등록"""
    # image.file.read() --> 업로드 파일 내부의 실제 파일 객체를 열어서 내용을 전부 읽어
    #                       bytes(0과 1로 나열)로 가져온다.
    row = image.file.read()

    # image.filename --> 사용자가 업로드한 원래 파일 이름
    result = register_book_service(isbn, raw, image.filename, db)
    
    if result.status == 'invalid_isbn':
        raise HTTPException(422, result.message)
    if result.status == 'duplicate':
        raise HTTPException(status.HTTP_409_CONFLICT, _duplicate_detail(result.book))
    if result.status == 'invalid_image':
        # 상태 코드 415 --> Unsupported Media Type (파일 형식이 이미지가 아니다.)
        raise HTTPException(415, result.message)

    return result.book

@app.get('/books')
def list_books(db: Session=Depends(get_db)):
    """등록된 책 전체 목록을 돌려주는 API"""
    return db.scalars(select(Book)).all()

# 새로 추가된 HTML(Jinja2) 라우터--------------------------------------------------
@app.get('/ui/books/lookup') 
def ui_lookup_form(request: Request):
    """GET: 조회 폼 화면만 보여준다."""
    # request: Request -> Jinja2Templates가 화면을 만들 때 반드시 필요로 하는 매개변수
    # 내부적으로 어떤 요청이 어떤 서비스/포트로 왔는지 등을 알아야 url_for() 같은 기능이 동작한다.
    # templates.TemplatesResponse(...) --> context에 담긴 데이터를 채워 넣은 뒤,
    #       완성된 html을 브라우저에 응답으로 보낸다.
    # context={} --> 맨 처음 화면 진입 시 조회 결과가 없으므로
    return templates.TemplateResponse(request=request, name='lookup.html', context={})

@app.post('/ui/books/lookup') 
def ui_lookup_submit(request: Request, isbn: str=Form(...), db: Session=Depends(get_db)):
    """POST: 폼 제출을 받아서 book_service 를 호출, 결과를 같은 화면에 다시 보여준다."""
    result = lookup_book_service(isbn, db)
    return templates.TemplateResponse(
        request=request,
        name='lookup.html',
        # context로 넘긴 값들을 lookup.html 안에서 {( result )}, {( isbn_input )} 
        context={'result': result, 'isbn_input': isbn}
    )

@app.get('/ui/books/register')
def ui_register_form(request:Request):
    return templates.TemplateResponse(request=request, name='register.html', context={})

@app.post('/ui/books/register')
def ui_register_submit(
    request: Request,
    isbn: str = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    raw = image.file.read()
    result = register_book_service(isbn, raw, image.filename, db)
    return templates.TemplateResponse(
        request=request,
        name='register.html',
        context={'result': result, 'isbn_input': isbn},
    )

@app.get('/shelf')
def shelf(request: Request, db: Session = Depends(get_db)):
    # .order_by(Book.created_at.desc()) --> 등록된 시각(creat_at) 기준으로 최신순(내림차순) 정렬
    books = db.scalars(select(Book).order_by(Book.created_at.desc())).all()

    shelf_items = []

    for book in books:
        cover_url = None # 책  표지 없음으로 미리 설정
        if book.cover_path:
            cover_url=f'/uploads/{Path(book.cover_path).name}' # 파일명만(확장자 포함)
        shelf_items.append({'book': book, 'cover_url': cover_url})

    return templates.TemplateResponse(
            request=request,
            name='shelf.html',
            context={'shelf_items': shelf_items},
        )