# 온톨로지 예제 실습

이 디렉토리에는 온톨로지 학습을 위한 예제 파일들이 있습니다.

## 📁 파일 목록

### 1. Turtle 온톨로지 파일

#### `family-ontology.ttl`
가족 관계 온톨로지 예제
- 3세대 가족 구조 (조부모, 부모, 자녀)
- 클래스: Person, Male, Female, Parent, Child
- 속성: hasParent, hasChild, hasSpouse, hasSibling, hasGrandparent
- 데이터 속성: hasName, hasAge, hasBirthYear, hasGender

**학습 포인트**:
- 클래스 계층 구조
- 객체 속성 (Object Property)
- 역관계 (inverse)
- 대칭 속성 (Symmetric Property)

#### `fitness-ontology.ttl`
피트니스 센터 도메인 온톨로지
- 클래스: Trainer, Member, Exercise, Equipment, MuscleGroup
- 관계: teaches, performs, requires, targets, specializes
- 실제 Doubless 센터와 유사한 구조

**학습 포인트**:
- 도메인 모델링
- 복잡한 관계 표현
- 실전 활용 사례

### 2. Python 예제 코드

#### `rdf_basics.py`
rdflib 라이브러리를 사용한 RDF 기초

**예제 목록**:
1. 기본 트리플 생성 및 출력
2. 가족 온톨로지 프로그래밍
3. 그래프 쿼리 (Python API)
4. TTL 파일 로드 및 쿼리
5. SPARQL 쿼리
6. 간단한 추론 예제

**실행**:
```bash
pip install rdflib
python rdf_basics.py
```

#### `owlready2_example.py`
Owlready2를 사용한 온톨로지 생성 및 추론

**예제 목록**:
1. 온톨로지 생성 및 저장
2. 추론 엔진 사용 (Pellet)
3. 제약 조건 (Restrictions)
4. 피트니스 온톨로지 구현
5. SPARQL 쿼리

**실행**:
```bash
pip install owlready2
python owlready2_example.py
```

## 🚀 시작하기

### 1. 환경 설정

```bash
# Python 가상환경 생성 (선택사항)
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 필요한 라이브러리 설치
pip install rdflib owlready2
```

### 2. TTL 파일 열어보기

Turtle 파일은 텍스트 에디터로 직접 열어서 읽을 수 있습니다.

```bash
# 가족 온톨로지 보기
cat family-ontology.ttl

# 피트니스 온톨로지 보기
cat fitness-ontology.ttl
```

### 3. Python 예제 실행

```bash
# RDF 기초 예제 실행
python rdf_basics.py

# Owlready2 예제 실행
python owlready2_example.py
```

## 📖 학습 순서

### Week 1: RDF 기초
1. `family-ontology.ttl` 파일 읽고 이해하기
2. `rdf_basics.py` 실행하며 개념 익히기
3. 자신의 프로필을 RDF로 만들어보기

### Week 2: 온톨로지 생성
1. `fitness-ontology.ttl` 분석
2. `owlready2_example.py` 실행
3. 새로운 도메인 온톨로지 설계 (예: 음식, 영화 등)

### Week 3: 실전 프로젝트
1. Doubless 급여 시스템을 온톨로지로 모델링
2. 추론 규칙 정의
3. Python으로 데이터 쿼리

## 💡 실습 과제

### 과제 1: 자기소개 온톨로지
자신의 정보를 RDF로 표현하세요.
- 이름, 나이, 직업, 취미
- 가족 관계, 친구 관계
- Turtle 형식으로 저장

**파일**: `my-profile.ttl`

### 과제 2: 영화 온톨로지
영화 도메인 온톨로지를 만드세요.
- 클래스: Movie, Actor, Director, Genre
- 속성: actedIn, directed, hasGenre, hasRating
- 최소 3개 영화 인스턴스

**파일**: `movie-ontology.ttl`

### 과제 3: Python으로 쿼리
`rdf_basics.py`를 참고하여:
1. 자신이 만든 TTL 파일 로드
2. SPARQL로 특정 조건 쿼리
3. 결과 출력

**파일**: `my_query.py`

## 🔧 도구 추천

### Protégé
그래픽 온톨로지 편집기
- 다운로드: https://protege.stanford.edu/
- TTL 파일 시각화 가능
- 추론 엔진 내장
- OntoGraf 플러그인으로 그래프 시각화

### 온라인 검증 도구
- [RDF Validator](https://www.w3.org/RDF/Validator/)
- [Turtle Validator](https://www.ldf.fi/service/rdf-validator)

## 📝 참고 자료

### Turtle 문법 가이드
```turtle
# Prefix 정의
@prefix ex: <http://example.org/> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .

# 기본 트리플
ex:John foaf:name "John Smith" .

# 세미콜론으로 같은 주어 반복
ex:John foaf:name "John Smith" ;
        foaf:age 30 ;
        foaf:knows ex:Mary .

# 콤마로 같은 속성 반복
ex:John foaf:knows ex:Mary ,
                   ex:Bob ,
                   ex:Alice .

# 타입 축약 (rdf:type → a)
ex:John a foaf:Person .

# 리스트
ex:John ex:hasChildren (ex:Alice ex:Bob ex:Charlie) .
```

### 자주 사용하는 Namespace
- `rdf`: http://www.w3.org/1999/02/22-rdf-syntax-ns#
- `rdfs`: http://www.w3.org/2000/01/rdf-schema#
- `owl`: http://www.w3.org/2002/07/owl#
- `foaf`: http://xmlns.com/foaf/0.1/
- `xsd`: http://www.w3.org/2001/XMLSchema#

## 🐛 문제 해결

### TTL 파싱 에러
```python
# 에러: 파일을 찾을 수 없음
FileNotFoundError: family-ontology.ttl

# 해결: examples/ 디렉토리에서 실행
cd /path/to/study/ontology/examples
python rdf_basics.py
```

### 추론 엔진 설치 (Owlready2)
```bash
# Java가 필요합니다
java -version

# Java가 없으면 설치
# macOS
brew install openjdk

# Ubuntu
sudo apt-get install default-jre
```

## 📊 학습 진행 체크리스트

- [ ] Turtle 파일 읽고 이해
- [ ] rdf_basics.py 실행 성공
- [ ] owlready2_example.py 실행 성공
- [ ] 자기소개 온톨로지 작성
- [ ] 영화 온톨로지 작성
- [ ] SPARQL 쿼리 작성
- [ ] Protégé 설치 및 사용
- [ ] 추론 엔진 실행

---

**다음 단계**: `notes/` 디렉토리의 학습 노트 참고
