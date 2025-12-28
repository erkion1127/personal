"""
RDF 기초 실습 - rdflib 라이브러리 사용

설치:
pip install rdflib
"""

from rdflib import Graph, Namespace, Literal, URIRef, BNode
from rdflib.namespace import RDF, RDFS, FOAF, XSD


def example1_basic_triples():
    """예제 1: 기본 트리플 생성 및 출력"""
    print("=== 예제 1: 기본 RDF 트리플 ===\n")

    # 그래프 생성
    g = Graph()

    # Namespace 정의
    EX = Namespace("http://example.org/")
    g.bind("ex", EX)
    g.bind("foaf", FOAF)

    # 트리플 추가
    g.add((EX.John, RDF.type, FOAF.Person))
    g.add((EX.John, FOAF.name, Literal("John Smith")))
    g.add((EX.John, FOAF.age, Literal(30, datatype=XSD.integer)))
    g.add((EX.John, FOAF.mbox, URIRef("mailto:john@example.org")))

    # Turtle 형식으로 출력
    print(g.serialize(format='turtle'))
    print()


def example2_family_ontology():
    """예제 2: 가족 온톨로지"""
    print("=== 예제 2: 가족 관계 온톨로지 ===\n")

    g = Graph()

    # Namespace
    FAMILY = Namespace("http://example.org/family#")
    g.bind("family", FAMILY)
    g.bind("foaf", FOAF)

    # 부모 생성
    john = FAMILY.John
    mary = FAMILY.Mary

    g.add((john, RDF.type, FOAF.Person))
    g.add((john, FOAF.name, Literal("John Smith")))
    g.add((john, FOAF.age, Literal(45)))
    g.add((john, FOAF.gender, Literal("male")))

    g.add((mary, RDF.type, FOAF.Person))
    g.add((mary, FOAF.name, Literal("Mary Smith")))
    g.add((mary, FOAF.age, Literal(43)))
    g.add((mary, FOAF.gender, Literal("female")))

    # 배우자 관계
    g.add((john, FAMILY.spouseOf, mary))
    g.add((mary, FAMILY.spouseOf, john))

    # 자녀 추가
    bob = FAMILY.Bob
    g.add((bob, RDF.type, FOAF.Person))
    g.add((bob, FOAF.name, Literal("Bob Smith")))
    g.add((bob, FOAF.age, Literal(20)))
    g.add((bob, FOAF.gender, Literal("male")))

    # 부모-자녀 관계
    g.add((bob, FAMILY.hasParent, john))
    g.add((bob, FAMILY.hasParent, mary))
    g.add((john, FAMILY.hasChild, bob))
    g.add((mary, FAMILY.hasChild, bob))

    print(g.serialize(format='turtle'))
    print()


def example3_query_graph():
    """예제 3: 그래프 쿼리"""
    print("=== 예제 3: 그래프 쿼리 ===\n")

    g = Graph()
    EX = Namespace("http://example.org/")
    g.bind("ex", EX)

    # 데이터 추가
    people = [
        ("Alice", 25, "alice@example.org"),
        ("Bob", 30, "bob@example.org"),
        ("Charlie", 35, "charlie@example.org"),
    ]

    for name, age, email in people:
        person = EX[name]
        g.add((person, RDF.type, FOAF.Person))
        g.add((person, FOAF.name, Literal(name)))
        g.add((person, FOAF.age, Literal(age)))
        g.add((person, FOAF.mbox, URIRef(f"mailto:{email}")))

    # 쿼리 1: 모든 사람 이름 조회
    print("모든 사람:")
    for s, p, o in g.triples((None, FOAF.name, None)):
        print(f"  - {o}")
    print()

    # 쿼리 2: 30세 이상인 사람
    print("30세 이상:")
    for person in g.subjects(RDF.type, FOAF.Person):
        for age in g.objects(person, FOAF.age):
            if age.value >= 30:
                name = list(g.objects(person, FOAF.name))[0]
                print(f"  - {name} ({age}세)")
    print()


def example4_load_ttl_file():
    """예제 4: TTL 파일 로드 및 쿼리"""
    print("=== 예제 4: TTL 파일 로드 ===\n")

    g = Graph()

    # family-ontology.ttl 파일 로드
    try:
        g.parse("family-ontology.ttl", format="turtle")
        print(f"로드된 트리플 수: {len(g)}")
        print()

        # 모든 사람 조회
        print("온톨로지의 모든 사람:")
        FAMILY = Namespace("http://example.org/family#")

        for person in g.subjects(RDF.type, FAMILY.Person):
            # 이름 가져오기
            names = list(g.objects(person, FAMILY.hasName))
            if names:
                name = names[0]
                # 나이 가져오기
                ages = list(g.objects(person, FAMILY.hasAge))
                age = ages[0] if ages else "Unknown"
                print(f"  - {name} ({age}세)")
        print()

    except FileNotFoundError:
        print("family-ontology.ttl 파일을 찾을 수 없습니다.")
        print("examples/ 디렉토리에서 실행하세요.")
        print()


def example5_sparql_query():
    """예제 5: SPARQL 쿼리"""
    print("=== 예제 5: SPARQL 쿼리 ===\n")

    g = Graph()
    EX = Namespace("http://example.org/")
    g.bind("ex", EX)
    g.bind("foaf", FOAF)

    # 데이터 추가
    g.add((EX.Alice, RDF.type, FOAF.Person))
    g.add((EX.Alice, FOAF.name, Literal("Alice")))
    g.add((EX.Alice, FOAF.age, Literal(25)))
    g.add((EX.Alice, FOAF.knows, EX.Bob))

    g.add((EX.Bob, RDF.type, FOAF.Person))
    g.add((EX.Bob, FOAF.name, Literal("Bob")))
    g.add((EX.Bob, FOAF.age, Literal(30)))

    # SPARQL 쿼리
    query = """
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>

        SELECT ?name ?age
        WHERE {
            ?person a foaf:Person .
            ?person foaf:name ?name .
            ?person foaf:age ?age .
            FILTER (?age > 20)
        }
        ORDER BY ?age
    """

    print("SPARQL 쿼리 결과:")
    results = g.query(query)
    for row in results:
        print(f"  - {row.name} ({row.age}세)")
    print()


def example6_reasoning_example():
    """예제 6: 간단한 추론 예제"""
    print("=== 예제 6: 추론 예제 ===\n")

    g = Graph()
    EX = Namespace("http://example.org/")
    g.bind("ex", EX)

    # 스키마 정의
    g.add((EX.Parent, RDFS.subClassOf, EX.Person))
    g.add((EX.Mother, RDFS.subClassOf, EX.Parent))
    g.add((EX.Father, RDFS.subClassOf, EX.Parent))

    # 인스턴스
    g.add((EX.Mary, RDF.type, EX.Mother))

    # 명시적 지식
    print("명시적 지식:")
    for s, p, o in g.triples((EX.Mary, RDF.type, None)):
        print(f"  Mary is a {o.split('#')[-1]}")
    print()

    # 추론: Mary는 Mother → Parent → Person
    print("추론 가능한 지식:")
    print("  Mary is a Mother")
    print("  → Mary is a Parent (subClassOf)")
    print("  → Mary is a Person (subClassOf)")
    print()

    # 실제 추론을 위해서는 OWL reasoner 필요
    # (예: Owlready2, HermiT, Pellet)


def main():
    """모든 예제 실행"""
    print("RDF 기초 실습\n" + "="*50 + "\n")

    example1_basic_triples()
    example2_family_ontology()
    example3_query_graph()
    example4_load_ttl_file()
    example5_sparql_query()
    example6_reasoning_example()

    print("="*50)
    print("실습 완료!")


if __name__ == "__main__":
    main()
