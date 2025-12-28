# RDF (Resource Description Framework) 기초

## RDF란?

**RDF**는 웹 상의 자원(Resource)을 설명하기 위한 W3C 표준 데이터 모델입니다.

### 핵심 아이디어
- 모든 것을 **트리플(Triple)**로 표현
- **주어(Subject) - 술어(Predicate) - 목적어(Object)** 구조

```
John    loves    Mary
(주어)  (술어)   (목적어)
```

## RDF 트리플

### 구조
```
<Subject> <Predicate> <Object> .
```

### 각 요소의 역할

1. **Subject (주어)**: 설명하려는 자원
   - URI 또는 Blank Node

2. **Predicate (술어)**: 관계 또는 속성
   - 반드시 URI

3. **Object (목적어)**: 값 또는 다른 자원
   - URI, Blank Node, 또는 리터럴(Literal)

## RDF 표현 예제

### 1. 간단한 예제
```turtle
# Turtle 문법
@prefix ex: <http://example.org/> .

ex:John ex:hasAge 30 .
ex:John ex:hasName "John Smith" .
ex:John ex:worksAt ex:Google .
```

**의미**:
- John의 나이는 30이다
- John의 이름은 "John Smith"이다
- John은 Google에서 일한다

### 2. 그래프 표현

```
    ex:John
      |
      |-- ex:hasAge --> 30
      |-- ex:hasName --> "John Smith"
      |-- ex:worksAt --> ex:Google
```

## URI (Uniform Resource Identifier)

RDF에서는 모든 자원을 URI로 식별합니다.

### 왜 URI를 사용하는가?
1. **전역적 고유성**: 전 세계에서 유일
2. **역참조 가능**: HTTP URI는 정보 조회 가능
3. **확장성**: 새로운 자원 추가 용이

### URI 예제
```turtle
# 완전한 URI
<http://example.org/people/John> <http://example.org/hasAge> "30" .

# Prefix를 사용한 축약형
@prefix ex: <http://example.org/> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .

ex:John foaf:age 30 .
```

## RDF 리터럴 (Literal)

리터럴은 문자열, 숫자, 날짜 등의 구체적 값입니다.

### 종류

1. **Plain Literal** (일반 문자열)
```turtle
ex:John ex:name "John Smith" .
ex:John ex:name "John Smith"@en .  # 언어 태그
```

2. **Typed Literal** (타입 지정)
```turtle
ex:John ex:age "30"^^xsd:integer .
ex:John ex:height "175.5"^^xsd:float .
ex:John ex:birthdate "1990-01-01"^^xsd:date .
```

## RDF 직렬화 형식

RDF는 여러 형식으로 표현 가능합니다.

### 1. Turtle (Terse RDF Triple Language)
**장점**: 사람이 읽기 쉬움

```turtle
@prefix ex: <http://example.org/> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .

ex:John a foaf:Person ;
    foaf:name "John Smith" ;
    foaf:age 30 ;
    foaf:knows ex:Mary .

ex:Mary a foaf:Person ;
    foaf:name "Mary Johnson" .
```

### 2. N-Triples
**장점**: 파싱 간단, 라인별 독립적

```ntriples
<http://example.org/John> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://xmlns.com/foaf/0.1/Person> .
<http://example.org/John> <http://xmlns.com/foaf/0.1/name> "John Smith" .
<http://example.org/John> <http://xmlns.com/foaf/0.1/age> "30"^^<http://www.w3.org/2001/XMLSchema#integer> .
```

### 3. RDF/XML
**장점**: XML 도구 활용 가능

```xml
<?xml version="1.0"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns:foaf="http://xmlns.com/foaf/0.1/"
         xmlns:ex="http://example.org/">
  <foaf:Person rdf:about="http://example.org/John">
    <foaf:name>John Smith</foaf:name>
    <foaf:age rdf:datatype="http://www.w3.org/2001/XMLSchema#integer">30</foaf:age>
  </foaf:Person>
</rdf:RDF>
```

### 4. JSON-LD
**장점**: JSON과 호환, 웹 개발자 친화적

```json
{
  "@context": {
    "foaf": "http://xmlns.com/foaf/0.1/",
    "ex": "http://example.org/"
  },
  "@id": "ex:John",
  "@type": "foaf:Person",
  "foaf:name": "John Smith",
  "foaf:age": 30
}
```

## 실습: 가족 관계 RDF

### 시나리오
John과 Mary는 부부이고, Bob은 그들의 아들입니다.

### Turtle로 표현
```turtle
@prefix ex: <http://example.org/family#> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
@prefix rel: <http://purl.org/vocab/relationship/> .

# Person 정의
ex:John a foaf:Person ;
    foaf:name "John Smith" ;
    foaf:age 45 ;
    foaf:gender "male" ;
    rel:spouseOf ex:Mary ;
    rel:parentOf ex:Bob .

ex:Mary a foaf:Person ;
    foaf:name "Mary Smith" ;
    foaf:age 43 ;
    foaf:gender "female" ;
    rel:spouseOf ex:John ;
    rel:parentOf ex:Bob .

ex:Bob a foaf:Person ;
    foaf:name "Bob Smith" ;
    foaf:age 20 ;
    foaf:gender "male" ;
    rel:childOf ex:John ;
    rel:childOf ex:Mary .
```

### 그래프 시각화
```
       ex:John ──── rel:spouseOf ───→ ex:Mary
          |                              |
          |                              |
    rel:parentOf                   rel:parentOf
          |                              |
          ↓                              ↓
       ex:Bob ←──── rel:childOf ────────┘
```

## RDFS (RDF Schema)

RDFS는 RDF를 확장하여 클래스와 속성의 계층을 정의합니다.

### 주요 개념

1. **rdfs:Class** - 클래스 정의
2. **rdfs:subClassOf** - 클래스 계층
3. **rdf:Property** - 속성 정의
4. **rdfs:domain** - 속성의 주어 타입
5. **rdfs:range** - 속성의 목적어 타입

### 예제: 사람과 직업

```turtle
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex: <http://example.org/> .

# 클래스 정의
ex:Person rdf:type rdfs:Class .
ex:Employee rdfs:subClassOf ex:Person .
ex:Manager rdfs:subClassOf ex:Employee .

# 속성 정의
ex:worksAt rdf:type rdf:Property ;
    rdfs:domain ex:Employee ;
    rdfs:range ex:Company .

ex:manages rdf:type rdf:Property ;
    rdfs:domain ex:Manager ;
    rdfs:range ex:Employee .

# 인스턴스
ex:Company rdf:type rdfs:Class .
ex:Google rdf:type ex:Company .

ex:Alice rdf:type ex:Manager ;
    ex:worksAt ex:Google ;
    ex:manages ex:Bob .

ex:Bob rdf:type ex:Employee ;
    ex:worksAt ex:Google .
```

### 추론 결과
```
명시적: Alice rdf:type ex:Manager

추론:
- Alice rdf:type ex:Employee (Manager는 Employee의 하위클래스)
- Alice rdf:type ex:Person (Employee는 Person의 하위클래스)
```

## Python에서 RDF 사용

### rdflib 라이브러리

```python
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, FOAF

# 그래프 생성
g = Graph()

# Namespace 정의
EX = Namespace("http://example.org/")

# 트리플 추가
g.add((EX.John, RDF.type, FOAF.Person))
g.add((EX.John, FOAF.name, Literal("John Smith")))
g.add((EX.John, FOAF.age, Literal(30)))

# 직렬화
print(g.serialize(format='turtle'))

# 쿼리
for s, p, o in g:
    print(f"{s} {p} {o}")
```

## 실습 과제

1. **자신의 프로필을 RDF로 표현**
   - 이름, 나이, 이메일, 직업
   - Turtle 형식 사용

2. **피트니스 센터 데이터 RDF 변환**
   - Trainer, Member, Exercise 클래스
   - teaches, performs 관계
   - resources/fitness-example.ttl 파일 생성

3. **RDFS 스키마 작성**
   - 클래스 계층 정의
   - 속성 도메인/레인지 정의

## 핵심 요점

1. RDF는 **트리플 기반** 데이터 모델
2. **URI**로 자원 식별
3. 여러 **직렬화 형식** 지원 (Turtle, JSON-LD 등)
4. **RDFS**로 스키마 정의
5. **그래프 구조**로 자연스러운 연결

## 다음 학습

- **SPARQL**: RDF 쿼리 언어
- **OWL**: 더 강력한 표현력
- **추론**: RDFS 기반 추론 실습

---

**학습일**:
**완료 여부**: [ ]
**실습 완료**: [ ]
