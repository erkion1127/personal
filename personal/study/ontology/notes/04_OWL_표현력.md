# OWL (Web Ontology Language)

## OWL이란?

**OWL**은 RDF와 RDFS를 확장하여 더 풍부한 의미를 표현할 수 있는 온톨로지 언어입니다.

### RDF/RDFS의 한계
```turtle
# RDFS로는 표현 불가능한 것들:
# 1. "모든 사람은 정확히 2명의 생물학적 부모를 가진다"
# 2. "배우자 관계는 대칭적이다" (A의 배우자가 B면, B의 배우자도 A)
# 3. "hasParent와 hasChild는 역관계다"
# 4. "Manager는 최소 1명의 직원을 관리해야 한다"
```

### OWL의 장점
- **표현력**: 복잡한 개념과 제약 표현
- **추론**: 명시되지 않은 지식 유도
- **검증**: 온톨로지 일관성 체크
- **상호운용성**: W3C 표준

## OWL 2 프로파일

OWL 2는 3가지 프로파일을 제공합니다:

### 1. OWL 2 EL (Existential Limitation)
- **목적**: 대규모 온톨로지
- **추론**: 다항 시간 (빠름)
- **사용 사례**: SNOMED CT (의료), Gene Ontology

### 2. OWL 2 QL (Query Language)
- **목적**: 데이터베이스와 통합
- **추론**: SQL로 변환 가능
- **사용 사례**: 데이터 통합, 매핑

### 3. OWL 2 DL (Description Logic)
- **목적**: 최대 표현력
- **추론**: 결정 가능하지만 느릴 수 있음
- **사용 사례**: 복잡한 도메인 모델

## 기본 구성 요소

### 1. 클래스 (Class)

```turtle
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix ex: <http://example.org/> .

# 클래스 선언
ex:Person a owl:Class .
ex:Animal a owl:Class .

# 서로소 클래스 (Disjoint)
ex:Male a owl:Class ;
    owl:disjointWith ex:Female .
# → 어떤 것도 동시에 Male이면서 Female일 수 없음

# 동등 클래스 (Equivalent)
ex:Human a owl:Class ;
    owl:equivalentClass ex:Person .
```

### 2. 속성 (Property)

#### 객체 속성 (Object Property)
```turtle
ex:hasParent a owl:ObjectProperty ;
    rdfs:domain ex:Person ;
    rdfs:range ex:Person .

ex:hasChild a owl:ObjectProperty ;
    owl:inverseOf ex:hasParent .
# → X hasParent Y ⇔ Y hasChild X
```

#### 데이터 속성 (Datatype Property)
```turtle
ex:hasAge a owl:DatatypeProperty ;
    rdfs:domain ex:Person ;
    rdfs:range xsd:integer .

ex:hasName a owl:DatatypeProperty ;
    rdfs:domain ex:Person ;
    rdfs:range xsd:string .
```

## 속성의 특성

### 1. 함수 속성 (Functional Property)
```turtle
ex:hasBirthMother a owl:ObjectProperty ,
                    owl:FunctionalProperty .
# → 각 사람은 최대 1명의 생물학적 어머니를 가짐
```

### 2. 역함수 속성 (Inverse Functional)
```turtle
ex:hasSSN a owl:DatatypeProperty ,
            owl:InverseFunctionalProperty .
# → 각 SSN은 최대 1명의 사람에게 속함
# → SSN이 같으면 같은 사람
```

### 3. 대칭 속성 (Symmetric)
```turtle
ex:hasSpouse a owl:ObjectProperty ,
               owl:SymmetricProperty .
# → X hasSpouse Y ⇒ Y hasSpouse X
```

### 4. 추이 속성 (Transitive)
```turtle
ex:hasAncestor a owl:ObjectProperty ,
                 owl:TransitiveProperty .
# → X hasAncestor Y, Y hasAncestor Z ⇒ X hasAncestor Z
```

### 5. 비대칭 속성 (Asymmetric)
```turtle
ex:hasParent a owl:ObjectProperty ,
               owl:AsymmetricProperty .
# → X hasParent Y ⇒ NOT (Y hasParent X)
```

### 6. 반사 속성 (Reflexive)
```turtle
ex:knows a owl:ObjectProperty ,
           owl:ReflexiveProperty .
# → 모든 X에 대해 X knows X
```

### 7. 비반사 속성 (Irreflexive)
```turtle
ex:hasChild a owl:ObjectProperty ,
              owl:IrreflexiveProperty .
# → 어떤 X도 X hasChild X가 아님
```

## 제약 조건 (Restrictions)

### 1. 존재 제약 (Existential Quantification)

```turtle
# "모든 부모는 최소 1명의 자녀를 가진다"
ex:Parent a owl:Class ;
    owl:equivalentClass [
        a owl:Restriction ;
        owl:onProperty ex:hasChild ;
        owl:someValuesFrom ex:Person
    ] .
```

### 2. 전체 제약 (Universal Quantification)

```turtle
# "트레이너가 가르치는 모든 대상은 회원이어야 한다"
ex:Trainer a owl:Class ;
    rdfs:subClassOf [
        a owl:Restriction ;
        owl:onProperty ex:teaches ;
        owl:allValuesFrom ex:Member
    ] .
```

### 3. 개수 제약 (Cardinality)

```turtle
# "모든 사람은 정확히 2명의 생물학적 부모를 가진다"
ex:Person rdfs:subClassOf [
    a owl:Restriction ;
    owl:onProperty ex:hasBiologicalParent ;
    owl:cardinality 2
] .

# 최소 개수
ex:Manager rdfs:subClassOf [
    a owl:Restriction ;
    owl:onProperty ex:manages ;
    owl:minCardinality 1
] .

# 최대 개수
ex:Person rdfs:subClassOf [
    a owl:Restriction ;
    owl:onProperty ex:hasSpouse ;
    owl:maxCardinality 1
] .

# 정확한 개수
owl:cardinality 2        # 정확히 2개
owl:minCardinality 1     # 최소 1개
owl:maxCardinality 3     # 최대 3개
```

### 4. 값 제약 (Value Restriction)

```turtle
# "특정 값을 가져야 함"
ex:VIPMember rdfs:subClassOf [
    a owl:Restriction ;
    owl:onProperty ex:hasMembershipLevel ;
    owl:hasValue "VIP"
] .
```

## 클래스 표현식

### 1. 합집합 (Union)

```turtle
# "부모는 아버지이거나 어머니다"
ex:Parent owl:equivalentClass [
    a owl:Class ;
    owl:unionOf (ex:Father ex:Mother)
] .
```

### 2. 교집합 (Intersection)

```turtle
# "여성 트레이너"
ex:FemaleTrainer owl:equivalentClass [
    a owl:Class ;
    owl:intersectionOf (ex:Female ex:Trainer)
] .
```

### 3. 여집합 (Complement)

```turtle
# "성인 = 사람 - 어린이"
ex:Adult owl:equivalentClass [
    a owl:Class ;
    owl:intersectionOf (
        ex:Person
        [ owl:complementOf ex:Child ]
    )
] .
```

### 4. 열거 (Enumeration)

```turtle
# "요일은 정확히 7개"
ex:DayOfWeek owl:equivalentClass [
    a owl:Class ;
    owl:oneOf (
        ex:Monday ex:Tuesday ex:Wednesday
        ex:Thursday ex:Friday ex:Saturday ex:Sunday
    )
] .
```

## 실전 예제

### 예제 1: 가족 온톨로지 (OWL 버전)

```turtle
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix family: <http://example.org/family#> .

# 클래스
family:Person a owl:Class .

family:Male a owl:Class ;
    rdfs:subClassOf family:Person ;
    owl:disjointWith family:Female .

family:Female a owl:Class ;
    rdfs:subClassOf family:Person .

# 부모 = 최소 1명의 자녀를 가진 사람
family:Parent owl:equivalentClass [
    a owl:Class ;
    owl:intersectionOf (
        family:Person
        [
            a owl:Restriction ;
            owl:onProperty family:hasChild ;
            owl:minCardinality 1
        ]
    )
] .

# 속성
family:hasParent a owl:ObjectProperty ;
    rdfs:domain family:Person ;
    rdfs:range family:Person .

family:hasChild a owl:ObjectProperty ;
    owl:inverseOf family:hasParent .

family:hasSpouse a owl:ObjectProperty ,
                   owl:SymmetricProperty ;
    rdfs:domain family:Person ;
    rdfs:range family:Person .

# 생물학적 부모는 정확히 2명
family:hasBiologicalParent a owl:ObjectProperty ;
    rdfs:subPropertyOf family:hasParent .

family:Person rdfs:subClassOf [
    a owl:Restriction ;
    owl:onProperty family:hasBiologicalParent ;
    owl:cardinality 2
] .

# 어머니는 여성이면서 부모
family:Mother owl:equivalentClass [
    owl:intersectionOf (family:Female family:Parent)
] .

# 아버지는 남성이면서 부모
family:Father owl:equivalentClass [
    owl:intersectionOf (family:Male family:Parent)
] .
```

### 예제 2: 피트니스 온톨로지 (OWL 버전)

```turtle
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix fitness: <http://example.org/fitness#> .

# 트레이너는 반드시 최소 1명의 회원을 가르쳐야 함
fitness:Trainer rdfs:subClassOf [
    a owl:Restriction ;
    owl:onProperty fitness:teaches ;
    owl:minCardinality 1
] .

# 트레이너가 가르치는 대상은 모두 회원
fitness:Trainer rdfs:subClassOf [
    a owl:Restriction ;
    owl:onProperty fitness:teaches ;
    owl:allValuesFrom fitness:Member
] .

# VIP 회원
fitness:VIPMember owl:equivalentClass [
    a owl:Class ;
    owl:intersectionOf (
        fitness:Member
        [
            a owl:Restriction ;
            owl:onProperty fitness:hasMembershipLevel ;
            owl:hasValue "VIP"
        ]
    )
] .

# 근력 운동은 최소 1개의 근육 그룹을 타겟해야 함
fitness:StrengthExercise rdfs:subClassOf [
    a owl:Restriction ;
    owl:onProperty fitness:targets ;
    owl:minCardinality 1
] .

# 운동이 필요로 하는 것은 모두 장비
fitness:Exercise rdfs:subClassOf [
    a owl:Restriction ;
    owl:onProperty fitness:requires ;
    owl:allValuesFrom fitness:Equipment
] .

# 회원의 남은 세션 수는 음수가 아님
fitness:Member rdfs:subClassOf [
    a owl:Restriction ;
    owl:onProperty fitness:hasSessions ;
    owl:allValuesFrom xsd:nonNegativeInteger
] .
```

## 추론 예시

### 명시적 지식
```turtle
ex:John ex:hasChild ex:Bob .
ex:Mary ex:hasChild ex:Bob .
```

### OWL 공리 (Axiom)
```turtle
ex:hasChild owl:inverseOf ex:hasParent .
```

### 추론된 지식
```turtle
# 자동으로 유도됨
ex:Bob ex:hasParent ex:John .
ex:Bob ex:hasParent ex:Mary .
```

### 일관성 체크

```turtle
# 정의: Male과 Female은 서로소
ex:Male owl:disjointWith ex:Female .

# 데이터
ex:Alice a ex:Male, ex:Female .  # ❌ 일관성 오류!
```

추론 엔진이 이를 감지하고 오류 보고

## OWL과 추론 엔진

### 주요 추론 엔진
1. **HermiT** - OWL 2 DL
2. **Pellet** - OWL 2
3. **Fact++** - OWL 2 DL
4. **ELK** - OWL 2 EL (빠름)

### 추론 종류
1. **클래스 계층 추론**: SubClassOf 관계 계산
2. **인스턴스 분류**: 개체가 속하는 클래스 추론
3. **속성 추론**: inverseOf, Symmetric, Transitive
4. **일관성 체크**: 모순 탐지

## Protégé에서 OWL 사용

### 1. 클래스 생성
```
1. Classes 탭
2. Add subclass
3. 속성 설정 (Equivalent to, Disjoint with)
```

### 2. 제약 조건 추가
```
1. Description 섹션에서 +
2. Restriction 선택
3. Property와 조건 선택
```

### 3. 추론 실행
```
1. Reasoner → HermiT
2. Start reasoner
3. Inferred hierarchy 확인
```

## 실습 과제

### 과제 1: 회사 온톨로지
다음을 OWL로 표현하세요:
- "Manager는 최소 1명의 직원을 관리한다"
- "CEO는 정확히 1명이다"
- "직원은 최대 1명의 관리자를 가진다"

### 과제 2: 교통 온톨로지
다음을 모델링하세요:
- Vehicle 클래스 (Car, Truck, Motorcycle)
- "모든 차량은 엔진을 가진다"
- "전기차는 배터리를 가진다"

### 과제 3: 추론 실습
1. inverseOf, SymmetricProperty 사용
2. Protégé에서 추론 실행
3. 추론된 지식 확인

## 핵심 요점

1. OWL은 **RDF/RDFS보다 강력한 표현력**
2. **제약 조건**으로 도메인 규칙 정의
3. **추론 엔진**으로 암묵적 지식 발견
4. **일관성 체크**로 오류 감지
5. **3가지 프로파일** - 목적에 맞게 선택

## 참고 자료

- [OWL 2 Primer (W3C)](https://www.w3.org/TR/owl2-primer/)
- [OWL 2 Quick Reference](https://www.w3.org/TR/owl2-quick-reference/)
- [Protégé OWL Tutorial](https://protegewiki.stanford.edu/wiki/ProtegeOWLTutorial)

---

**학습일**:
**완료 여부**: [ ]
**Protégé 실습**: [ ]
