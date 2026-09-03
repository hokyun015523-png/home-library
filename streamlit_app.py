'''
home_library_v3 / streamlit_app.py
------------------------------------
Docker 결합 시 변경 사항
- import os 추가
- API 주소를 하드코딩 대신 os.getenv()로 사용해서 "환경변수가 있다면 그 값,
    없으면 기존 로컬 기본값(localhost)"를 사용하도록 설정
'''
import os
import requests
import streamlit as st

API = os.getenv('API_URL', 'http://localhost:8000') 

st.title('우리집 책장 (개발 중)')

st.header('1단계: ISBN으로 바로 조회해보기')
st.caption('사진 없이 ISBN 숫자만 넣어서, 서지정보 API가 잘 연결됐는지 먼저 확인합니다.')

isbn_input = st.text_input('ISBN 입력 (예: 9791139721973)')

def show_response(r: requests.Response):
    """
    API 응답을 상태코드별로 다르게 보여주는 공용 함수 
    """
    if r.ok:  # 성공
        st.success(f'등록됨: {r.json()["title"]}')
        return

    if r.status_code == 409:  # 중복
        existing = r.json()['detail']['existing_book']
        st.info(
            f'이미 서재에 있는 책이에요!\n\n'
            f'{existing["title"]}\n\n'
            f'저자: {existing["author"] or "정보 없음"}\n'
            f'출판사: {existing["publisher"] or "정보 없음"}'
        )
        return

    # 그 외 - 에러
    detail = r.json().get('detail', '')
    st.error(f'실패 {r.status_code} : {detail}')

if st.button('조회 후 등록'):
    if not isbn_input:
        st.warning('ISBN을 입력해주세요!')
    else:
        r = requests.get(f'{API}/books/lookup', params={'isbn': isbn_input})
        show_response(r)

st.divider()  # 구분선

# 2단계 : ISBN + 표지 사진을 한 폼에서 함께 등록
st.header('2단계: ISBN + 표지 사진 함께 등록하기')

with st.form('register_form'):
    form_isbn = st.text_input('ISBN 입력')
    form_image = st.file_uploader('표지 사진')
    submitted = st.form_submit_button('등록하기')

if submitted:
    if not form_isbn:
        st.warning('ISBN을 입력해주세요!')
    elif form_image is None:
        st.warning('표지 사진을 선택해주세요!')
    else:
        r = requests.post(
            f'{API}/books/register',
            data={'isbn': form_isbn},
            files={'image': (form_image.name, form_image.getvalue(), form_image.type)},
        )
        show_response(r)

st.divider()

st.subheader('등록된 책')
for book in requests.get(f'{API}/books').json():
    st.write(f'{book["title"]} ({book["recognition_status"]})')