# GraphDB Docker POC 가이드

## 개요

GraphDB Free Edition을 Docker로 빠르게 시작하는 가이드입니다.
완전 무료이며, 20분 내에 시작할 수 있습니다.

## 준비물

- Docker Desktop
- 8GB+ RAM
- 10GB+ 디스크 공간

## 1단계: Docker 설치 확인 (2분)

```bash
# Docker 버전 확인
docker --version
# Docker version 20.10.x

# Docker Compose 버전 확인
docker-compose --version
# docker-compose version 1.29.x
```

## 2단계: GraphDB 실행 (3분)

### 방법 1: Docker Run (빠름)

```bash
# GraphDB Free Edition 실행
docker run -d \
  --name graphdb \
  -p 7200:7200 \
  -v $(pwd)/graphdb-data:/opt/graphdb/home \
  ontotext/graphdb:10.7.0

# 로그 확인
docker logs -f graphdb
```

### 방법 2: Docker Compose (권장)

```yaml
# docker-compose.yml
version: '3.8'

services:
  graphdb:
    image: ontotext/graphdb:10.7.0
    container_name: graphdb-poc
    ports:
      - "7200:7200"
    volumes:
      - ./graphdb-data:/opt/graphdb/home
      - ./graphdb-import:/root/graphdb-import
    environment:
      - GDB_HEAP_SIZE=4G
      - GDB_JAVA_OPTS=-Xmx4g -Xms4g
    restart: unless-stopped
```

```bash
# 실행
docker-compose up -d

# 상태 확인
docker-compose ps
```

## 3단계: 웹 UI 접속 (1분)

```
브라우저에서 접속:
http://localhost:7200

초기 설정:
- 라이선스 동의 (Free Edition)
- 관리자 계정 생성 (선택 사항)
```

## 4단계: Repository 생성 (3분)

### UI에서 생성

```
1. Setup → Repositories
2. "Create new repository" 클릭
3. Repository ID: fitness-ontology
4. Repository title: Fitness POC
5. Ruleset: OWL-Horst (Optimized)
6. "Create" 클릭
```

### REST API로 생성

```bash
curl -X POST \
  http://localhost:7200/rest/repositories \
  -H 'Content-Type: application/json' \
  -d '{
    "id": "fitness-ontology",
    "title": "Fitness POC",
    "type": "free-repository",
    "params": {
      "ruleset": {
        "label": "Ruleset",
        "name": "ruleset",
        "value": "owl-horst-optimized"
      }
    }
  }'
```

## 5단계: 온톨로지 로드 (5분)

### 방법 1: UI Upload

```
1. Import → RDF
2. Upload RDF files 선택
3. family-ontology.ttl 또는 fitness-ontology.ttl 선택
4. Import settings:
   - Base URI: http://example.org/
   - Named graph: (default)
5. "Import" 클릭
```

### 방법 2: cURL Upload

```bash
# TTL 파일 업로드
curl -X POST \
  -H "Content-Type: application/x-turtle" \
  --data-binary @family-ontology.ttl \
  "http://localhost:7200/repositories/fitness-ontology/statements"
```

### 방법 3: Python Script

```python
# load_ontology.py
import requests

GRAPHDB_URL = "http://localhost:7200"
REPO_ID = "fitness-ontology"

def load_ttl_file(filepath, base_uri="http://example.org/"):
    with open(filepath, 'rb') as f:
        data = f.read()

    response = requests.post(
        f"{GRAPHDB_URL}/repositories/{REPO_ID}/statements",
        data=data,
        headers={
            "Content-Type": "application/x-turtle"
        },
        params={
            "baseURI": base_uri
        }
    )

    if response.status_code == 204:
        print(f"✅ Successfully loaded {filepath}")
    else:
        print(f"❌ Error: {response.text}")

# 사용
load_ttl_file("family-ontology.ttl")
load_ttl_file("fitness-ontology.ttl")
```

## 6단계: SPARQL 쿼리 (5분)

### UI에서 쿼리

```
1. SPARQL 탭 클릭
2. 쿼리 작성
3. Run 버튼 클릭
```

**예제 쿼리**:
```sparql
PREFIX fitness: <http://example.org/fitness#>

SELECT ?trainerName (COUNT(?member) AS ?memberCount)
WHERE {
    ?member fitness:trainedBy ?trainer .
    ?trainer fitness:hasName ?trainerName .
}
GROUP BY ?trainerName
ORDER BY DESC(?memberCount)
```

### Python으로 쿼리

```python
# query_graphdb.py
import requests
import json

GRAPHDB_URL = "http://localhost:7200"
REPO_ID = "fitness-ontology"

def sparql_query(query):
    response = requests.post(
        f"{GRAPHDB_URL}/repositories/{REPO_ID}",
        data={"query": query},
        headers={"Accept": "application/sparql-results+json"}
    )

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Query failed: {response.text}")

# 예제 사용
query = """
PREFIX foaf: <http://xmlns.com/foaf/0.1/>

SELECT ?name ?age
WHERE {
    ?person foaf:name ?name ;
            foaf:age ?age .
    FILTER (?age > 30)
}
ORDER BY ?age
"""

results = sparql_query(query)

# 결과 출력
for binding in results['results']['bindings']:
    name = binding['name']['value']
    age = binding['age']['value']
    print(f"{name}: {age}세")
```

## 7단계: 추론 활성화 (2분)

### 추론 확인

```sparql
# 추론 전후 비교
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX ex: <http://example.org/>

# 명시적 타입만
SELECT ?person ?type
WHERE {
    ?person a ?type .
}

# 추론된 타입 포함 (자동)
# GraphDB는 기본적으로 추론 활성화됨
```

### 추론 규칙 확인

```
UI → Setup → Repositories → fitness-ontology
→ Edit → Ruleset 확인
```

**사용 가능한 Ruleset**:
- `rdfs`: RDFS 추론
- `owl-horst`: OWL Horst (빠름)
- `owl-max`: OWL 2 최대 (느림)
- `owl-2-rl`: OWL 2 RL (권장)

## 8단계: 성능 모니터링

### 시스템 상태 확인

```bash
# GraphDB 메모리 사용량
curl http://localhost:7200/rest/monitor/infrastructure

# Repository 통계
curl http://localhost:7200/rest/repositories/fitness-ontology/size
```

### 쿼리 성능 분석

```sparql
# SPARQL 쿼리에 EXPLAIN 추가
EXPLAIN
SELECT ?s ?p ?o
WHERE {
    ?s ?p ?o .
}
LIMIT 10
```

## 완전한 POC 스크립트

```python
# graphdb_poc.py
import requests
import json
from typing import List, Dict

class GraphDBClient:
    def __init__(self, base_url="http://localhost:7200", repo_id="fitness-ontology"):
        self.base_url = base_url
        self.repo_id = repo_id
        self.repo_url = f"{base_url}/repositories/{repo_id}"

    def create_repository(self, ruleset="owl-horst-optimized"):
        """Repository 생성"""
        config = {
            "id": self.repo_id,
            "title": f"{self.repo_id} POC",
            "type": "free-repository",
            "params": {
                "ruleset": {
                    "label": "Ruleset",
                    "name": "ruleset",
                    "value": ruleset
                }
            }
        }

        response = requests.post(
            f"{self.base_url}/rest/repositories",
            json=config
        )

        if response.status_code == 201:
            print(f"✅ Repository '{self.repo_id}' created")
        else:
            print(f"Repository may already exist: {response.text}")

    def load_file(self, filepath: str, base_uri="http://example.org/"):
        """TTL 파일 로드"""
        with open(filepath, 'rb') as f:
            data = f.read()

        response = requests.post(
            f"{self.repo_url}/statements",
            data=data,
            headers={"Content-Type": "application/x-turtle"},
            params={"baseURI": base_uri}
        )

        if response.status_code == 204:
            print(f"✅ Loaded {filepath}")
            return True
        else:
            print(f"❌ Error loading {filepath}: {response.text}")
            return False

    def query(self, sparql: str) -> Dict:
        """SPARQL SELECT 쿼리"""
        response = requests.post(
            self.repo_url,
            data={"query": sparql},
            headers={"Accept": "application/sparql-results+json"}
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Query failed: {response.text}")

    def update(self, sparql: str) -> bool:
        """SPARQL UPDATE"""
        response = requests.post(
            f"{self.repo_url}/statements",
            data={"update": sparql},
            headers={"Content-Type": "application/sparql-update"}
        )

        return response.status_code == 204

    def get_size(self) -> int:
        """트리플 개수 확인"""
        response = requests.get(f"{self.repo_url}/size")
        return int(response.text)

    def clear(self):
        """모든 데이터 삭제"""
        response = requests.delete(f"{self.repo_url}/statements")
        return response.status_code == 204

# 사용 예제
if __name__ == "__main__":
    client = GraphDBClient()

    # 1. Repository 생성
    client.create_repository()

    # 2. 온톨로지 로드
    client.load_file("family-ontology.ttl")
    client.load_file("fitness-ontology.ttl")

    # 3. 트리플 개수 확인
    size = client.get_size()
    print(f"\nTotal triples: {size}")

    # 4. 쿼리 실행
    query = """
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>

    SELECT ?name ?age
    WHERE {
        ?person foaf:name ?name ;
                foaf:age ?age .
    }
    ORDER BY ?age
    LIMIT 10
    """

    results = client.query(query)

    print("\nQuery Results:")
    for binding in results['results']['bindings']:
        name = binding['name']['value']
        age = binding['age']['value']
        print(f"  {name}: {age}세")

    # 5. 데이터 추가
    insert = """
    PREFIX ex: <http://example.org/>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>

    INSERT DATA {
        ex:NewPerson a foaf:Person ;
            foaf:name "New Person" ;
            foaf:age 25 .
    }
    """

    if client.update(insert):
        print("\n✅ Data inserted")
        print(f"New total triples: {client.get_size()}")
```

## Docker Compose 전체 스택

```yaml
# docker-compose-full.yml
version: '3.8'

services:
  graphdb:
    image: ontotext/graphdb:10.7.0
    container_name: graphdb
    ports:
      - "7200:7200"
    volumes:
      - graphdb-data:/opt/graphdb/home
      - ./ontologies:/root/graphdb-import
    environment:
      - GDB_HEAP_SIZE=4G

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - GRAPHDB_URL=http://graphdb:7200
      - GRAPHDB_REPO=fitness-ontology
    depends_on:
      - graphdb

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  graphdb-data:
```

## 비용

- **GraphDB Free Edition**: $0
- **인프라 (Docker)**: $0
- **총 비용**: $0

**제한사항**:
- 1억 트리플 제한
- 상업적 사용 시 라이선스 필요

## 업그레이드 경로

GraphDB Free → Standard → Enterprise

**Standard Edition** (~$10K/year):
- 무제한 트리플
- 이메일 지원
- 상업적 사용 가능

**Enterprise Edition** (~$30K/year):
- 클러스터링
- 핫 백업
- 24/7 지원

## 문제 해결

### 메모리 부족
```yaml
# docker-compose.yml에서 메모리 증가
environment:
  - GDB_HEAP_SIZE=8G
  - GDB_JAVA_OPTS=-Xmx8g -Xms8g
```

### 데이터 지속성
```bash
# Volume 확인
docker volume ls

# 백업
docker run --rm \
  -v graphdb-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/graphdb-backup.tar.gz /data
```

## 다음 단계

1. **프로덕션 배포**
   - Kubernetes 배포
   - 고가용성 설정

2. **통합 개발**
   - FastAPI/Spring Boot
   - React 대시보드

3. **고급 기능**
   - Full-text search
   - GraphQL endpoint

## 참고 자료

- [GraphDB Documentation](https://graphdb.ontotext.com/documentation/)
- [GraphDB Docker](https://hub.docker.com/r/ontotext/graphdb)
- [SPARQL Tutorial](https://graphdb.ontotext.com/documentation/10.7/sparql.html)

---

**소요 시간**: 20-30분
**예상 비용**: $0
**난이도**: ⭐⭐⭐☆☆
