# Agentic AI 스터디

Agentic AI, 온톨로지, 지식 그래프 등 AI 에이전트 관련 스터디 자료 모음

## 📚 스터디 주제

### 1. Ontology (온톨로지)
**디렉토리**: `ontology/`

지식 표현 및 온톨로지 이론 학습
- 온톨로지 개념 및 이론
- OWL (Web Ontology Language)
- RDF/RDFS
- 도메인 온톨로지 설계
- 추론(Reasoning) 엔진

**학습 순서**:
1. 온톨로지 기초 개념
2. RDF 트리플 구조 이해
3. OWL 문법 및 활용
4. Protégé 도구 사용법
5. 실전 온톨로지 모델링

### 2. Agentic AI (에이전트 AI)
**디렉토리**: `agentic-ai/`

자율 에이전트 시스템 학습
- AI 에이전트 아키텍처
- ReAct (Reasoning + Acting) 패턴
- Chain-of-Thought (CoT)
- Tool Use & Function Calling
- Multi-Agent Systems
- 에이전트 평가 및 벤치마크

**학습 순서**:
1. 에이전트 기본 개념 및 역사
2. ReAct 패러다임 이해
3. 도구 사용 패턴
4. 멀티 에이전트 협업
5. 실전 프로젝트

### 3. LLM Fundamentals (LLM 기초)
**디렉토리**: `llm-fundamentals/`

대규모 언어 모델 기초 학습
- Transformer 아키텍처
- Attention 메커니즘
- Fine-tuning vs RAG
- Prompt Engineering
- Context Window & Memory
- Token Economics

**학습 순서**:
1. Transformer 구조 이해
2. Attention 메커니즘
3. 프롬프트 엔지니어링 기법
4. RAG 시스템 구축
5. 성능 최적화

### 4. Agent Frameworks (에이전트 프레임워크)
**디렉토리**: `agent-frameworks/`

주요 에이전트 프레임워크 실습
- LangChain
- LangGraph
- AutoGen
- CrewAI
- Semantic Kernel
- Anthropic MCP

**학습 순서**:
1. LangChain 기초 및 실습
2. LangGraph 상태 기반 에이전트
3. AutoGen 멀티 에이전트
4. MCP 서버 구축
5. 프레임워크 비교 분석

### 5. Knowledge Graphs (지식 그래프)
**디렉토리**: `knowledge-graphs/`

지식 그래프 구축 및 활용
- Neo4j 그래프 데이터베이스
- GraphRAG
- 지식 추출(Knowledge Extraction)
- 엔티티 링킹
- 그래프 쿼리 언어 (Cypher)

**학습 순서**:
1. 그래프 데이터베이스 개념
2. Neo4j 설치 및 기본 사용
3. Cypher 쿼리 언어
4. 지식 그래프 구축 파이프라인
5. GraphRAG 구현

### 6. Reasoning Systems (추론 시스템)
**디렉토리**: `reasoning-systems/`

논리적 추론 및 의사결정 시스템
- 기호 추론 (Symbolic Reasoning)
- 신경-기호 통합 (Neuro-Symbolic AI)
- Planning & Decision Making
- Constraint Satisfaction
- 인과 추론 (Causal Reasoning)

**학습 순서**:
1. 기호 추론 기초
2. 논리 프로그래밍 (Prolog)
3. 계획 수립 알고리즘
4. 신경-기호 통합 기법
5. 실전 응용

## 🗂️ 폴더 구조

```
study/
├── README.md                      # 이 파일
├── ontology/                      # 온톨로지 스터디
│   ├── 00_시작하기.md
│   ├── notes/                    # 학습 노트
│   ├── examples/                 # 예제 코드
│   └── resources/                # 참고 자료
├── agentic-ai/                   # Agentic AI 스터디
│   ├── 00_시작하기.md
│   ├── notes/
│   ├── examples/
│   └── projects/                 # 실습 프로젝트
├── llm-fundamentals/             # LLM 기초
│   ├── 00_시작하기.md
│   ├── notes/
│   └── experiments/              # 실험 코드
├── agent-frameworks/             # 프레임워크 실습
│   ├── 00_시작하기.md
│   ├── langchain/
│   ├── langgraph/
│   ├── autogen/
│   └── mcp/
├── knowledge-graphs/             # 지식 그래프
│   ├── 00_시작하기.md
│   ├── notes/
│   ├── neo4j-examples/
│   └── graph-rag/
└── reasoning-systems/            # 추론 시스템
    ├── 00_시작하기.md
    ├── notes/
    ├── symbolic/
    └── neuro-symbolic/
```

## 📖 스터디 방법

### 1. 학습 노트 작성
각 주제별 `notes/` 디렉토리에 학습 내용 정리
- 날짜별 파일: `YYYY-MM-DD-주제.md`
- 개념 정리, 코드 스니펫, 참고 링크 포함

### 2. 실습 코드 관리
`examples/` 또는 `projects/` 디렉토리에 실습 코드 저장
- 주제별 하위 디렉토리 생성
- README.md로 실행 방법 문서화

### 3. 참고 자료 수집
`resources/` 디렉토리에 논문, 블로그 링크, 도서 정보 정리
- `papers.md`: 논문 목록 및 요약
- `articles.md`: 블로그/아티클 링크
- `books.md`: 추천 도서 목록

### 4. 진행 상황 추적
각 주제별 `00_시작하기.md`에 학습 진행 상황 체크리스트 관리

## 🎯 학습 로드맵

### Phase 1: 기초 다지기 (1-2개월)
1. LLM Fundamentals - Transformer & Attention
2. Agentic AI - 기본 개념 및 ReAct
3. Agent Frameworks - LangChain 기초

### Phase 2: 심화 학습 (2-3개월)
1. Ontology - RDF/OWL 이론 및 실습
2. Knowledge Graphs - Neo4j & GraphRAG
3. Agent Frameworks - LangGraph, AutoGen

### Phase 3: 고급 주제 (3-4개월)
1. Reasoning Systems - 신경-기호 통합
2. Multi-Agent Systems - 협업 에이전트
3. 실전 프로젝트 - 통합 시스템 구축

## 📌 추천 학습 자료

### 온라인 강의
- Coursera: "Knowledge Graphs"
- DeepLearning.AI: "LangChain for LLM Application Development"
- Stanford CS224W: "Machine Learning with Graphs"

### 논문
- "ReAct: Synergizing Reasoning and Acting in Language Models"
- "Attention Is All You Need"
- "Knowledge Graphs" (Hogan et al., 2021)

### 도서
- "Semantic Web for the Working Ontologist"
- "Building LLM Apps"
- "Hands-On Graph Neural Networks"

### 커뮤니티
- LangChain Discord
- r/LanguageTechnology
- Papers With Code

## 💡 팁

1. **꾸준함이 중요**: 매일 30분씩 꾸준히 학습
2. **실습 위주**: 이론만 보지 말고 직접 코드 작성
3. **문서화 습관**: 배운 내용을 정리하며 이해도 향상
4. **커뮤니티 활용**: 막힐 때 질문하고 토론하기
5. **프로젝트 중심**: 학습한 내용을 실제 프로젝트에 적용

## 📅 학습 일지 템플릿

각 주제의 `notes/` 디렉토리에 아래 템플릿 사용:

```markdown
# YYYY-MM-DD - 학습 주제

## 학습 목표
- [ ] 목표 1
- [ ] 목표 2

## 학습 내용
### 개념 정리
...

### 핵심 코드
```python
# 예제 코드
```

## 참고 자료
- [링크](url)

## 다음 학습 계획
...

## 질문/이슈
...
```
