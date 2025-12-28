# SPARQL 쿼리 언어

## SPARQL이란?

**SPARQL** (SPARQL Protocol and RDF Query Language)은 RDF 데이터를 조회하고 조작하기 위한 표준 쿼리 언어입니다.

> SQL : 관계형 데이터베이스 = SPARQL : RDF 데이터

### 특징
- W3C 표준 (2008년 권고안)
- 패턴 매칭 기반
- 그래프 구조 쿼리에 최적화
- HTTP 프로토콜로 원격 쿼리 가능

## 기본 쿼리 구조

```sparql
PREFIX ex: <http://example.org/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>

SELECT ?name ?age
WHERE {
    ?person a foaf:Person .
    ?person foaf:name ?name .
    ?person foaf:age ?age .
}
```

### 구성 요소
1. **PREFIX**: Namespace 선언
2. **SELECT**: 반환할 변수 지정
3. **WHERE**: 패턴 매칭 조건

## 변수와 패턴

### 변수
- `?변수명` 또는 `$변수명`
- 예: `?person`, `?name`, `?age`

### 트리플 패턴
```sparql
# 기본 패턴
?subject ?predicate ?object .

# 구체적인 예
?person foaf:name "John Smith" .
ex:John foaf:age ?age .
```

### 세미콜론과 콤마
```sparql
# 세미콜론: 같은 주어
?person foaf:name ?name ;
        foaf:age ?age ;
        foaf:knows ?friend .

# 콤마: 같은 주어와 술어
?person foaf:knows ?friend1, ?friend2, ?friend3 .
```

## SPARQL 쿼리 형식

### 1. SELECT - 데이터 조회

```sparql
PREFIX foaf: <http://xmlns.com/foaf/0.1/>

SELECT ?name ?email
WHERE {
    ?person foaf:name ?name .
    ?person foaf:mbox ?email .
}
```

**결과**:
```
name            email
"Alice"         "alice@example.org"
"Bob"           "bob@example.org"
```

### 2. ASK - 존재 여부 확인

```sparql
PREFIX foaf: <http://xmlns.com/foaf/0.1/>

ASK {
    ?person foaf:name "Alice" .
}
```

**결과**: `true` 또는 `false`

### 3. CONSTRUCT - 새 그래프 생성

```sparql
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX ex: <http://example.org/>

CONSTRUCT {
    ?person ex:fullName ?name .
}
WHERE {
    ?person foaf:name ?name .
}
```

**결과**: 새로운 RDF 트리플 생성

### 4. DESCRIBE - 리소스 설명

```sparql
DESCRIBE <http://example.org/John>
```

**결과**: 해당 리소스의 모든 트리플 반환

## 필터링 (FILTER)

### 비교 연산자
```sparql
SELECT ?name ?age
WHERE {
    ?person foaf:name ?name ;
            foaf:age ?age .
    FILTER (?age > 30)
}
```

### 문자열 함수
```sparql
SELECT ?name
WHERE {
    ?person foaf:name ?name .
    FILTER (CONTAINS(?name, "John"))
}

# 정규식
FILTER (REGEX(?name, "^John", "i"))  # i = case insensitive
```

### 논리 연산자
```sparql
FILTER (?age >= 18 && ?age <= 65)
FILTER (?name = "Alice" || ?name = "Bob")
FILTER (!BOUND(?email))  # email이 없는 경우
```

## OPTIONAL - 선택적 패턴

```sparql
SELECT ?name ?email
WHERE {
    ?person foaf:name ?name .
    OPTIONAL { ?person foaf:mbox ?email }
}
```

- `email`이 있으면 반환, 없어도 `?name`은 반환
- SQL의 LEFT JOIN과 유사

## UNION - 합집합

```sparql
SELECT ?contact
WHERE {
    { ?person foaf:mbox ?contact }
    UNION
    { ?person foaf:phone ?contact }
}
```

## 정렬 및 제한

### ORDER BY - 정렬
```sparql
SELECT ?name ?age
WHERE {
    ?person foaf:name ?name ;
            foaf:age ?age .
}
ORDER BY DESC(?age)  # 내림차순
# ORDER BY ?age       # 오름차순 (기본)
```

### LIMIT / OFFSET - 페이징
```sparql
SELECT ?name
WHERE {
    ?person foaf:name ?name .
}
ORDER BY ?name
LIMIT 10      # 상위 10개
OFFSET 20     # 20개 건너뛰기
```

## 집계 함수

```sparql
# COUNT - 개수
SELECT (COUNT(?person) AS ?total)
WHERE {
    ?person a foaf:Person .
}

# AVG - 평균
SELECT (AVG(?age) AS ?avgAge)
WHERE {
    ?person foaf:age ?age .
}

# MIN, MAX - 최소, 최대
SELECT (MIN(?age) AS ?youngest) (MAX(?age) AS ?oldest)
WHERE {
    ?person foaf:age ?age .
}

# SUM - 합계
SELECT (SUM(?salary) AS ?totalSalary)
WHERE {
    ?person ex:salary ?salary .
}
```

## GROUP BY - 그룹화

```sparql
PREFIX ex: <http://example.org/>

SELECT ?company (COUNT(?employee) AS ?count)
WHERE {
    ?employee ex:worksAt ?company .
}
GROUP BY ?company
```

### HAVING - 그룹 필터링
```sparql
SELECT ?company (COUNT(?employee) AS ?count)
WHERE {
    ?employee ex:worksAt ?company .
}
GROUP BY ?company
HAVING (COUNT(?employee) > 10)
```

## 경로 표현식 (Property Paths)

### 기본 경로
```sparql
# 직접 연결
?person foaf:knows ?friend .

# 역방향
?person ^foaf:knows ?knower .  # ?knower foaf:knows ?person

# 시퀀스
?person foaf:knows/foaf:knows ?friendOfFriend .
```

### 반복 경로
```sparql
# 0회 이상 반복 (*)
?person foaf:knows* ?connection .

# 1회 이상 반복 (+)
?person foaf:knows+ ?connection .

# 0회 또는 1회 (?)
?person foaf:knows? ?maybeKnows .
```

### 대체 경로
```sparql
# OR
?person (foaf:mbox|foaf:phone) ?contact .
```

## 실전 예제

### 예제 1: 가족 관계 쿼리

```sparql
PREFIX family: <http://example.org/family#>

# 모든 부모-자녀 쌍
SELECT ?parentName ?childName
WHERE {
    ?child family:hasParent ?parent .
    ?parent family:hasName ?parentName .
    ?child family:hasName ?childName .
}

# 조부모 찾기 (경로 사용)
SELECT ?grandparentName ?grandchildName
WHERE {
    ?grandchild family:hasParent/family:hasParent ?grandparent .
    ?grandparent family:hasName ?grandparentName .
    ?grandchild family:hasName ?grandchildName .
}

# 형제자매 찾기
SELECT ?person1Name ?person2Name
WHERE {
    ?person1 family:hasParent ?parent .
    ?person2 family:hasParent ?parent .
    FILTER (?person1 != ?person2)
    ?person1 family:hasName ?person1Name .
    ?person2 family:hasName ?person2Name .
}
```

### 예제 2: 피트니스 센터 쿼리

```sparql
PREFIX fitness: <http://example.org/fitness#>

# 트레이너별 회원 수
SELECT ?trainerName (COUNT(?member) AS ?memberCount)
WHERE {
    ?member fitness:trainedBy ?trainer .
    ?trainer fitness:hasName ?trainerName .
}
GROUP BY ?trainerName
ORDER BY DESC(?memberCount)

# 특정 운동을 하는 회원들
SELECT ?memberName ?sessionsLeft
WHERE {
    ?member fitness:performs fitness:BenchPress ;
            fitness:hasName ?memberName ;
            fitness:hasSessions ?sessionsLeft .
}
ORDER BY ?sessionsLeft

# 바벨이 필요한 모든 운동
SELECT DISTINCT ?exerciseName
WHERE {
    ?exercise fitness:requires fitness:Barbell ;
              fitness:hasName ?exerciseName .
}

# VIP 회원 중 20회 이상 남은 회원
SELECT ?name ?sessions
WHERE {
    ?member fitness:hasMembershipLevel "VIP" ;
            fitness:hasSessions ?sessions ;
            fitness:hasName ?name .
    FILTER (?sessions >= 20)
}
```

### 예제 3: 복잡한 분석 쿼리

```sparql
PREFIX fitness: <http://example.org/fitness#>

# 각 근육 그룹별로 얼마나 많은 운동이 타겟하는지
SELECT ?muscleGroup (COUNT(?exercise) AS ?exerciseCount)
WHERE {
    ?exercise fitness:targets ?muscleGroup .
}
GROUP BY ?muscleGroup
ORDER BY DESC(?exerciseCount)

# 트레이너의 전문 운동과 그것을 하는 회원 매칭
SELECT ?trainerName ?exerciseName ?memberName
WHERE {
    ?trainer fitness:specializes ?exercise ;
             fitness:hasName ?trainerName .
    ?member fitness:trainedBy ?trainer ;
            fitness:performs ?exercise ;
            fitness:hasName ?memberName .
    ?exercise fitness:hasName ?exerciseName .
}
```

## SPARQL 함수

### 문자열 함수
```sparql
STRLEN(?string)           # 길이
SUBSTR(?string, 1, 5)     # 부분 문자열
UCASE(?string)            # 대문자
LCASE(?string)            # 소문자
CONCAT(?str1, " ", ?str2) # 연결
CONTAINS(?string, "test") # 포함 여부
STRSTARTS(?string, "A")   # 시작 확인
STRENDS(?string, "Z")     # 끝 확인
```

### 숫자 함수
```sparql
ABS(?number)              # 절대값
ROUND(?number)            # 반올림
CEIL(?number)             # 올림
FLOOR(?number)            # 내림
RAND()                    # 난수 (0-1)
```

### 날짜/시간 함수
```sparql
NOW()                     # 현재 시간
YEAR(?datetime)           # 년도 추출
MONTH(?datetime)          # 월 추출
DAY(?datetime)            # 일 추출
```

### 타입 변환
```sparql
STR(?value)               # 문자열 변환
xsd:integer(?string)      # 정수 변환
xsd:float(?string)        # 실수 변환
```

## Federated Query (연합 쿼리)

여러 SPARQL 엔드포인트를 동시에 쿼리:

```sparql
PREFIX dbpedia: <http://dbpedia.org/resource/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>

SELECT ?name ?abstract
WHERE {
    ?person foaf:name ?name .

    SERVICE <http://dbpedia.org/sparql> {
        ?dbpediaPerson foaf:name ?name ;
                       dbpedia:abstract ?abstract .
        FILTER (LANG(?abstract) = "en")
    }
}
```

## UPDATE 연산 (SPARQL 1.1)

### INSERT - 데이터 추가
```sparql
PREFIX ex: <http://example.org/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>

INSERT DATA {
    ex:NewPerson a foaf:Person ;
                 foaf:name "New Person" ;
                 foaf:age 25 .
}
```

### DELETE - 데이터 삭제
```sparql
DELETE DATA {
    ex:OldPerson foaf:age 30 .
}
```

### DELETE/INSERT - 수정
```sparql
DELETE { ?person foaf:age ?oldAge }
INSERT { ?person foaf:age ?newAge }
WHERE {
    ?person foaf:name "John" ;
            foaf:age ?oldAge .
    BIND(?oldAge + 1 AS ?newAge)
}
```

## 디버깅 팁

### 1. 단계적으로 쿼리 작성
```sparql
# Step 1: 기본 패턴
SELECT ?person
WHERE {
    ?person a foaf:Person .
}

# Step 2: 속성 추가
SELECT ?person ?name
WHERE {
    ?person a foaf:Person ;
            foaf:name ?name .
}

# Step 3: 필터 추가
SELECT ?person ?name ?age
WHERE {
    ?person a foaf:Person ;
            foaf:name ?name ;
            foaf:age ?age .
    FILTER (?age > 30)
}
```

### 2. 중간 결과 확인
```sparql
SELECT *  # 모든 변수 확인
WHERE {
    # 쿼리 패턴
}
LIMIT 10  # 일부만 보기
```

## 실습 과제

### 과제 1: 기본 쿼리
1. 모든 사람의 이름과 나이 조회
2. 30세 이상인 사람만 필터링
3. 나이 순으로 정렬

### 과제 2: 집계
1. 전체 사람 수 계산
2. 평균 나이 계산
3. 회사별 직원 수 집계

### 과제 3: 복잡한 쿼리
1. 친구의 친구 찾기 (경로 사용)
2. 같은 회사에 다니는 사람들의 네트워크
3. 공통 관심사를 가진 사람 찾기

## 참고 자료

- [SPARQL 1.1 Query Language (W3C)](https://www.w3.org/TR/sparql11-query/)
- [SPARQL by Example](https://www.w3.org/2009/Talks/0615-qbe/)
- [Learning SPARQL (Book)](http://learningsparql.com/)

---

**학습일**:
**완료 여부**: [ ]
**실습 완료**: [ ]
