'''
home_library_v1 / services/recognition.py
-------------------------------------------
국립중앙도서관 소장자료 검색 API 버전
'''
import json
import os
import re
import urllib.parse
import urllib.request
from dotenv import load_dotenv

def normalize_isbn(value: str) -> str | None:
    """
    isbn 10자리, 13자리에 따라서 체크섬
    """
    digits = re.sub(r'[^0-9Xx]', '', value)

    if len(digits) == 10:
        total = sum(
            (10 - i) * (10 if c.upper() == 'X' else int(c))
            for i, c in enumerate(digits)
        )
        return digits.upper() if total % 11 == 0 else None

    if len(digits) == 13:
        total = sum(
            int(c) * (1 if i % 2 == 0 else 3)
            for i, c in enumerate(digits[:12])
        )
        check_digit = (10 - total % 10) % 10
        return digits if check_digit == int(digits[-1]) else None

    return None

def extract_isbn(image_path) -> str | None:
    """
    isbn 바코드(이미지 경로)가 들어왔을 때 올바른 isbn 체크섬
    """
    try:
        import pytesseract
        from PIL import Image, ImageEnhance, ImageOps
    except ImportError:
        return None

    with Image.open(image_path) as source:
        image = ImageOps.grayscale(source)
        image = ImageEnhance.Contrast(image).enhance(2)
        try:
            text = pytesseract.image_to_string(image, config='--psm 11')
        except pytesseract.TesseractNotFoundError:
            return None

    for candidate in re.findall(r'(?:97[89][\s-]?)?[0-9][0-9Xx\s-]{8,16}', text):
        isbn = normalize_isbn(candidate)
        if isbn:
            return isbn

    return None

load_dotenv()

# 국립 중앙도서관 인증키
NLK_SEARCH_KEY = os.environ.get('NLK_SEARCH_KEY', '')
# print(NLK_SEARCH_KEY)
NLK_SEARCH_URL = 'https://www.nl.go.kr/NL/search/openApi/search.do'


def clean_title(raw_title: str | None) -> str | None:
    """순수 제목 추출"""
    if not raw_title:
        return None
    return raw_title.split(' : ')[0].strip()


def clean_author(raw_author: str | None) -> str | None:
    if not raw_author:
        return None
    cleaned = re.sub(r'[가-힣]{2,4}\s*:\s*', '', raw_author)
    return cleaned.strip()


def clean_publisher(raw_pub: str | None) -> str | None:
    if not raw_pub:
        return None
    parts = [p.strip() for p in raw_pub.split(':') if p.strip()]
    return parts[-1] if parts else None


def lookup_metadata(isbn: str) -> dict | None:
    """
    책에 관한 메타데이터를 가지고 isbn, 책 제목, 책 저자, 출판사 반환
    """
    if not NLK_SEARCH_KEY:
        return None

    params = {
        'key': NLK_SEARCH_KEY,
        'detailSearch': 'true',
        'isbnOp': 'isbn',
        'isbnCode': isbn,
        'apiType': 'json',
    }
    url = f'{NLK_SEARCH_URL}?{urllib.parse.urlencode(params)}'

    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            payload = json.load(response)
    except (OSError, ValueError):
        return None

    results = payload.get('result') or []
    if not results:
        return None

    item = results[0]

    title = clean_title(item.get('titleInfo'))
    if not title:
        return None

    return {
        'isbn': item.get('isbn', isbn),
        'title': title,
        'author': clean_author(item.get('authorInfo')),
        'publisher': clean_publisher(item.get('pubInfo')),
    }
