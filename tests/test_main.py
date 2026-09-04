'''
home_library/tests/teat_main.py 
-----------------------------------
GitHub Actions 실습용 최초 테스트 v5
- DB, 외부 API(국립중앙도서관 api key) 없어도 통과하는 순수 로직만 검증한다.
- 검증 대상
    services/recognition.py 의 normalize_isbn() 함수
    (유효한 ISBN인지 체크섬으로 확인하는 함수)
- 이 파일이 GinHub Actions(CI)에서 push할 때마다 자종으로 실행된다
'''
from services.recognition import normalize_isbn

def test_하이픈이_있는_isbn13을_숫자로_정리한다():
    # 하이픈을 제거하고 순수 숫자 13자리 문자열로 반환되는지 확인한다.
    assert normalize_isbn('978-89-6626-318-9')  == '9788966263189'

def test_체크섬이_틀린_isbn은_none을_반환한다():
    # 마지막 자리만 9만 0으로 바꿔서 체크섬이 깨지도록 해본다
    # normalize_isbn은 숫자처럼 보이지만 가짜인 ISBN을 여기서 걸러내야 한다.
    assert normalize_isbn('978-89-6626-3182-0') is None
