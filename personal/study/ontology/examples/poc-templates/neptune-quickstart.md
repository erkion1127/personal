# Amazon Neptune 빠른 시작 가이드

## 개요

Amazon Neptune은 AWS의 완전 관리형 그래프 데이터베이스입니다.
30분 내에 시작할 수 있습니다.

## 1단계: AWS 계정 준비 (5분)

### 필요한 것
- AWS 계정
- AWS CLI 설치 (선택)
- 신용카드

### AWS Console 접속
1. https://aws.amazon.com/ 접속
2. 로그인 또는 계정 생성
3. Neptune 서비스 검색

## 2단계: Neptune 클러스터 생성 (10분)

### Console에서 생성

```
1. Neptune 콘솔 접속
2. "Create database" 클릭
3. 설정:
   - DB cluster identifier: my-ontology-poc
   - DB instance class: db.r5.large (최소)
   - VPC: 기본값
   - Public accessibility: Yes (POC용)
4. "Create database" 클릭
5. 생성 대기 (약 10분)
```

### CloudFormation으로 생성 (권장)

```bash
# CloudFormation 템플릿 다운로드
curl -O https://s3.amazonaws.com/aws-neptune-customer-samples/neptune-sagemaker/cloudformation-templates/neptune-sagemaker/neptune-sagemaker.json

# 스택 생성
aws cloudformation create-stack \
  --stack-name neptune-poc \
  --template-body file://neptune-sagemaker.json \
  --parameters \
    ParameterKey=DBClusterIdentifier,ParameterValue=my-ontology-poc \
    ParameterKey=NeptuneQueryTimeout,ParameterValue=120000 \
  --capabilities CAPABILITY_IAM
```

## 3단계: 연결 설정 (5분)

### 엔드포인트 확인

```bash
# Console에서 확인 또는 CLI
aws neptune describe-db-clusters \
  --db-cluster-identifier my-ontology-poc \
  --query 'DBClusters[0].Endpoint' \
  --output text
```

**결과 예시**:
```
my-ontology-poc.cluster-xxxxx.us-east-1.neptune.amazonaws.com
```

### 보안 그룹 설정

```
1. EC2 Console → Security Groups
2. Neptune 보안 그룹 선택
3. Inbound rules → Edit
4. Add rule:
   - Type: Custom TCP
   - Port: 8182
   - Source: My IP (또는 0.0.0.0/0 for POC)
5. Save rules
```

## 4단계: 데이터 로드 (5분)

### 방법 1: S3 Bulk Loader (권장)

```python
import boto3

# S3에 RDF 파일 업로드
s3 = boto3.client('s3')
s3.upload_file(
    'family-ontology.ttl',
    'my-ontology-bucket',
    'data/family-ontology.ttl'
)

# Neptune Loader 실행
import requests

NEPTUNE_ENDPOINT = "your-neptune-endpoint:8182"
S3_URI = "s3://my-ontology-bucket/data/"

response = requests.post(
    f"https://{NEPTUNE_ENDPOINT}/loader",
    json={
        "source": S3_URI,
        "format": "turtle",
        "iamRoleArn": "your-iam-role-arn",
        "region": "us-east-1",
        "failOnError": "FALSE"
    }
)

print(response.json())
```

### 방법 2: SPARQL UPDATE (소규모)

```python
from gremlin_python.driver import client as gremlin_client

# 연결
client = gremlin_client.Client(
    f'wss://{NEPTUNE_ENDPOINT}/sparql',
    'g'
)

# 데이터 삽입
sparql_insert = """
PREFIX ex: <http://example.org/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>

INSERT DATA {
    ex:John a foaf:Person ;
        foaf:name "John Smith" ;
        foaf:age 45 .

    ex:Mary a foaf:Person ;
        foaf:name "Mary Smith" ;
        foaf:age 43 .

    ex:Bob a foaf:Person ;
        foaf:name "Bob Smith" ;
        foaf:age 20 ;
        ex:hasParent ex:John, ex:Mary .
}
"""

# 실행
requests.post(
    f"https://{NEPTUNE_ENDPOINT}/sparql",
    data={"update": sparql_insert}
)
```

## 5단계: 쿼리 실행 (5분)

### Python으로 쿼리

```python
# neptune_query.py
import requests

NEPTUNE_ENDPOINT = "your-neptune-endpoint:8182"

def run_sparql_query(query):
    response = requests.post(
        f"https://{NEPTUNE_ENDPOINT}/sparql",
        data={"query": query},
        headers={"Accept": "application/sparql-results+json"}
    )
    return response.json()

# 예제 쿼리
query = """
PREFIX foaf: <http://xmlns.com/foaf/0.1/>

SELECT ?name ?age
WHERE {
    ?person a foaf:Person ;
            foaf:name ?name ;
            foaf:age ?age .
}
ORDER BY ?age
"""

results = run_sparql_query(query)
print(results)
```

### cURL로 쿼리

```bash
curl -X POST \
  https://your-neptune-endpoint:8182/sparql \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'query=SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10'
```

## 6단계: 성능 모니터링

### CloudWatch 메트릭

```
- CPUUtilization
- FreeableMemory
- SparqlRequestsPerSec
- MainRequestQueueDepth
```

### 로그 확인

```bash
# 감사 로그 활성화
aws neptune modify-db-cluster \
  --db-cluster-identifier my-ontology-poc \
  --cloudwatch-logs-export-configuration \
    '{"EnableLogTypes":["audit"]}'
```

## 비용 최적화

### 개발/테스트 환경

```
인스턴스 타입: db.t3.medium
예상 비용: ~$0.082/hour = ~$60/month
스토리지: $0.10/GB/month
```

### 스케줄링 (비용 절감)

```python
# Lambda로 야간 정지 스케줄링
import boto3

def lambda_handler(event, context):
    neptune = boto3.client('neptune')

    # 밤 11시: 중지
    if event['action'] == 'stop':
        neptune.stop_db_cluster(
            DBClusterIdentifier='my-ontology-poc'
        )

    # 아침 9시: 시작
    elif event['action'] == 'start':
        neptune.start_db_cluster(
            DBClusterIdentifier='my-ontology-poc'
        )
```

## 완전한 예제 코드

```python
# neptune_poc.py
import requests
import json

class NeptuneClient:
    def __init__(self, endpoint):
        self.endpoint = endpoint
        self.sparql_url = f"https://{endpoint}/sparql"

    def query(self, sparql):
        """SPARQL SELECT 쿼리"""
        response = requests.post(
            self.sparql_url,
            data={"query": sparql},
            headers={"Accept": "application/sparql-results+json"}
        )
        return response.json()

    def update(self, sparql):
        """SPARQL UPDATE 쿼리"""
        response = requests.post(
            self.sparql_url,
            data={"update": sparql}
        )
        return response.status_code == 200

    def load_from_s3(self, s3_uri, format="turtle", iam_role_arn=None):
        """S3에서 데이터 로드"""
        loader_url = f"https://{self.endpoint}/loader"
        payload = {
            "source": s3_uri,
            "format": format,
            "iamRoleArn": iam_role_arn,
            "region": "us-east-1",
            "failOnError": "FALSE"
        }
        response = requests.post(loader_url, json=payload)
        return response.json()

# 사용 예제
if __name__ == "__main__":
    client = NeptuneClient("your-neptune-endpoint:8182")

    # 데이터 삽입
    insert_query = """
    PREFIX ex: <http://example.org/>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>

    INSERT DATA {
        ex:Alice a foaf:Person ;
            foaf:name "Alice" ;
            foaf:age 25 .
    }
    """
    client.update(insert_query)

    # 쿼리
    select_query = """
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>

    SELECT ?name ?age
    WHERE {
        ?person foaf:name ?name ;
                foaf:age ?age .
    }
    """
    results = client.query(select_query)
    print(json.dumps(results, indent=2))
```

## 문제 해결

### 연결 실패
```bash
# 보안 그룹 확인
aws ec2 describe-security-groups \
  --group-ids sg-xxxxx

# VPC 엔드포인트 확인
aws neptune describe-db-clusters \
  --db-cluster-identifier my-ontology-poc
```

### 쿼리 타임아웃
```bash
# 타임아웃 설정 증가
aws neptune modify-db-cluster-parameter-group \
  --db-cluster-parameter-group-name default.neptune1.2 \
  --parameters "ParameterName=neptune_query_timeout,ParameterValue=180000,ApplyMethod=immediate"
```

## 다음 단계

1. **추론 설정**
   - Neptune ML 활용
   - SPARQL 1.1 규칙

2. **통합 개발**
   - Lambda 함수 작성
   - API Gateway 연결

3. **프로덕션 준비**
   - Multi-AZ 설정
   - 백업 전략
   - 모니터링 대시보드

## 참고 자료

- [Neptune Developer Guide](https://docs.aws.amazon.com/neptune/)
- [SPARQL 1.1 Query Language](https://www.w3.org/TR/sparql11-query/)
- [Neptune Samples](https://github.com/aws/graph-notebook)

---

**소요 시간**: 30-60분
**예상 비용**: ~$60-100/month (테스트용)
**난이도**: ⭐⭐☆☆☆
