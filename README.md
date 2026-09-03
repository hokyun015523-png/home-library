# CI (Continuous Integration)란?
- CI(지속적 통합)는 코드를 push할 때마다 자동으로 품질 검사를 수행하는 프로세스

개발자 코드 변경 push -> 코드 스타일 점검 Lint -> pytest 검사 Test -> Docker Build -> 결과 통보(Pass/Fail)

---

## 왜 CI가 필요한가??

### 문제 상황
1. 코드 스타일 -> 팀원마다 다른 스타일 
2. 테스트 누락 -> "테스트 돌려봤어??" 물어봐야 한다.
3. 빌드 실패 -> 배포 후 발견
4. 코드 리뷰 -> 스타일 지적에 시간 소모

### CI 있으면
1. ruff가 자동 검사
2. push마다 자동 실행
3. PR 단계에서 차단
4. 자동화된 부분은 생략

### CI의 가치
> CI는 "문제를 빨리 발견하는 것"이 핵심이다.
코드를 Push한 직후 문제를 발견하면 수정이 쉽지만, 배포 후에 발견하면 롤백, 긴급 대응, 고객 영향 등 비용이 기하급수적으로 커진다.

---

# Github Actions 기본 구조
- Github Actions 워크플로우는 YAML 파일로 정의한다.
- 깃허브는 `.github/workflows/` 경로의 YAML 파일을 자동으로 인식한다.

```
.github/workflows/ci파일.yml
```

---

## YAML 파일

### YAML이란??
- YAML Ain't Markup Language는 사람이 읽고 쓰기 쉽게 만들어진 설정 파일 형식
- 프로그램에게 어떻게 동작할지 알려주는 설정값을 적을 때 사용
- 보통 읽을 때 '야믈' 또는 '야말' 이런식으로 읽는다. 
- YAML 은 프로그래밍 언어가 아니라 '정리된 메모'라고 생각한다.
- 들여쓰기만 잘 맞추면 파이썬 코드보다 쉽다.
- 괄호나 따옴표가 거의 없어서 사람이 보기에 가장 깔끔하다. 

### 핵심 규칙 3가지
#### 1. `키:값` 으로 데이터를 표현한다.
```yaml
name: Test
```
-> `name` 이라는 키에 `Test` 라는 값을 준다는 뜻.
- 콜론 뒤에 공백 한 칸 필수!

#### 2. 들여쓰기(space)로 계층 구조를 표현한다.
```yaml
jobs:
  test:
    runs-on: ubuntu-latest
```
- `jobs`보다 `test`가 한 단계 더 안쪽 (`test`는 `jobs`에 속한 항목)
- `runs-on`이 `test`보다 더 안쪽 (`test`에 속한 세부 설정)
- 탭(Tab) 키를 누르면 에러가 나는 경우가 많다.(스페이스바로 사용하는 것을 권장)

#### 3. `-` 은 리스트(목록)를 뜻한다.
```yaml
on:
  - push
  - pull_request
```
- `on`이라는 키의 값이 `push`, `pull_request` 여러개 라는 뜻(배열)


### YAML의 기본 구조
```yaml
name: CI이름    # 워크플로우 이름(Actions 탭에 표시)

on:                    # 언제 실행할 것인가? (트리거)
  push:                # 코드 push 할 때
    branches: [main]   # main 브랜치에 push할 때만
  pull_request:        # PR 생성 / 업데이트 시 
    branches: [main]

jobs:                   # 무엇을 실행할 것인가?
  job-name:             # 작업 이름
    runs-on: ubuntu-latest   # 어디서 실행할 것인가?(가상 머신)
    steps:                   # 실행 단계들 (순차 실행)
      - uses: actions/checkout@v4   # 코드 체크 아웃
      - run: echo "Hello CI"        # 쉘 명령어 실행
```

