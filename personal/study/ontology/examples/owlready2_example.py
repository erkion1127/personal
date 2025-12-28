"""
Owlready2를 사용한 온톨로지 생성 및 추론 예제

설치:
pip install owlready2
"""

from owlready2 import *


def example1_create_ontology():
    """예제 1: 온톨로지 생성"""
    print("=== 예제 1: 온톨로지 생성 ===\n")

    # 새 온톨로지 생성
    onto = get_ontology("http://example.org/family.owl")

    with onto:
        # 클래스 정의
        class Person(Thing):
            pass

        class Male(Person):
            pass

        class Female(Person):
            pass

        # 속성 정의
        class hasParent(ObjectProperty):
            domain = [Person]
            range = [Person]

        class hasChild(ObjectProperty):
            inverse_property = hasParent

        class hasName(DataProperty):
            domain = [Person]
            range = [str]

        class hasAge(DataProperty):
            domain = [Person]
            range = [int]

        # 인스턴스 생성
        john = Male("John")
        john.hasName = ["John Smith"]
        john.hasAge = [45]

        mary = Female("Mary")
        mary.hasName = ["Mary Smith"]
        mary.hasAge = [43]

        bob = Male("Bob")
        bob.hasName = ["Bob Smith"]
        bob.hasAge = [20]
        bob.hasParent = [john, mary]

    # 저장
    onto.save(file="family_owlready.owl", format="rdfxml")
    print("온톨로지가 family_owlready.owl에 저장되었습니다.\n")

    # 확인
    print("생성된 인스턴스:")
    for individual in onto.individuals():
        print(f"  - {individual.name}: {individual.hasName}")
    print()


def example2_reasoning():
    """예제 2: 추론 엔진 사용"""
    print("=== 예제 2: 추론 엔진 ===\n")

    onto = get_ontology("http://example.org/reasoning.owl")

    with onto:
        class Person(Thing):
            pass

        class hasParent(ObjectProperty, TransitiveProperty):
            domain = [Person]
            range = [Person]

        class hasGrandparent(ObjectProperty):
            domain = [Person]
            range = [Person]
            # 추론 규칙: X hasParent Y, Y hasParent Z → X hasGrandparent Z

        # 인스턴스
        grandpa = Person("Grandpa")
        john = Person("John")
        bob = Person("Bob")

        john.hasParent = [grandpa]
        bob.hasParent = [john]

    print("추론 전:")
    print(f"  Bob의 부모: {bob.hasParent}")
    print(f"  Bob의 조부모: {bob.hasGrandparent if hasattr(bob, 'hasGrandparent') else '없음'}")
    print()

    # 추론 실행 (HermiT 또는 Pellet 필요)
    try:
        sync_reasoner_pellet(infer_property_values=True, infer_data_property_values=True)
        print("추론 후:")
        print(f"  Bob의 부모: {bob.hasParent}")

        # 추이 관계로 조부모까지 추론 가능
        all_ancestors = []
        for ancestor in bob.hasParent:
            all_ancestors.append(ancestor.name)
            if hasattr(ancestor, 'hasParent'):
                for grand in ancestor.hasParent:
                    all_ancestors.append(f"{grand.name} (조부모)")

        print(f"  추론된 조상: {all_ancestors}")
    except Exception as e:
        print(f"추론 엔진 오류: {e}")
        print("Pellet 또는 HermiT 설치가 필요할 수 있습니다.")
    print()


def example3_restrictions():
    """예제 3: 제약 조건 (Restrictions)"""
    print("=== 예제 3: 제약 조건 ===\n")

    onto = get_ontology("http://example.org/restrictions.owl")

    with onto:
        class Person(Thing):
            pass

        class Parent(Person):
            pass

        class hasChild(ObjectProperty):
            domain = [Person]
            range = [Person]

        # 제약: Parent는 최소 1명의 자녀를 가져야 함
        class Parent(Person):
            equivalent_to = [Person & hasChild.min(1, Person)]

        # 제약: 정확히 2명의 생물학적 부모
        class hasBiologicalParent(ObjectProperty):
            domain = [Person]
            range = [Person]

        class Person(Thing):
            is_a = [hasBiologicalParent.exactly(2, Person)]

        john = Parent("John")
        bob = Person("Bob")
        alice = Person("Alice")

        john.hasChild = [bob, alice]

    print("제약 조건 정의:")
    print("  - Parent는 최소 1명의 자녀를 가져야 함")
    print("  - Person은 정확히 2명의 생물학적 부모를 가짐")
    print()

    # 일관성 검사
    try:
        sync_reasoner_pellet()
        print("온톨로지가 일관성이 있습니다.")
    except OwlReadyInconsistentOntologyError:
        print("온톨로지에 일관성 오류가 있습니다!")
    except Exception as e:
        print(f"검증 중 오류: {e}")
    print()


def example4_fitness_ontology():
    """예제 4: 피트니스 온톨로지"""
    print("=== 예제 4: 피트니스 온톨로지 ===\n")

    onto = get_ontology("http://example.org/fitness.owl")

    with onto:
        # 클래스
        class Person(Thing):
            pass

        class Trainer(Person):
            pass

        class Member(Person):
            pass

        class Exercise(Thing):
            pass

        class Equipment(Thing):
            pass

        # 속성
        class teaches(ObjectProperty):
            domain = [Trainer]
            range = [Member]

        class performs(ObjectProperty):
            domain = [Member]
            range = [Exercise]

        class requires(ObjectProperty):
            domain = [Exercise]
            range = [Equipment]

        class hasName(DataProperty):
            domain = [Thing]
            range = [str]

        class hasSessions(DataProperty):
            domain = [Member]
            range = [int]

        # 인스턴스
        trainer_kim = Trainer("TrainerKim")
        trainer_kim.hasName = ["김철수"]

        member_park = Member("MemberPark")
        member_park.hasName = ["박민수"]
        member_park.hasSessions = [20]
        member_park.teaches = [trainer_kim]  # trainedBy의 역

        bench_press = Exercise("BenchPress")
        bench_press.hasName = ["벤치 프레스"]

        barbell = Equipment("Barbell")
        barbell.hasName = ["바벨"]

        bench_press.requires = [barbell]
        member_park.performs = [bench_press]

    print("피트니스 온톨로지:")
    print(f"  트레이너: {trainer_kim.hasName[0]}")
    print(f"  회원: {member_park.hasName[0]} (남은 세션: {member_park.hasSessions[0]})")
    print(f"  수행 운동: {bench_press.hasName[0]}")
    print(f"  필요 장비: {barbell.hasName[0]}")
    print()

    # 쿼리: 바벨이 필요한 모든 운동
    print("바벨이 필요한 운동:")
    for exercise in barbell.INDIRECT_requires:
        print(f"  - {exercise.hasName[0] if exercise.hasName else exercise.name}")
    print()


def example5_sparql_with_owlready():
    """예제 5: Owlready2에서 SPARQL 사용"""
    print("=== 예제 5: SPARQL 쿼리 ===\n")

    onto = get_ontology("http://example.org/people.owl")

    with onto:
        class Person(Thing):
            pass

        class hasName(DataProperty):
            domain = [Person]
            range = [str]

        class hasAge(DataProperty):
            domain = [Person]
            range = [int]

        # 사람들 생성
        for name, age in [("Alice", 25), ("Bob", 30), ("Charlie", 35)]:
            p = Person(name)
            p.hasName = [name]
            p.hasAge = [age]

    # SPARQL 쿼리
    query = """
        PREFIX onto: <http://example.org/people.owl#>

        SELECT ?person ?name ?age
        WHERE {
            ?person a onto:Person .
            ?person onto:hasName ?name .
            ?person onto:hasAge ?age .
            FILTER (?age >= 30)
        }
    """

    print("SPARQL 쿼리 결과 (30세 이상):")
    graph = default_world.as_rdflib_graph()
    results = list(graph.query(query))

    for row in results:
        print(f"  - {row}")
    print()


def main():
    """모든 예제 실행"""
    print("Owlready2 온톨로지 실습\n" + "="*50 + "\n")

    example1_create_ontology()
    example2_reasoning()
    example3_restrictions()
    example4_fitness_ontology()
    example5_sparql_with_owlready()

    print("="*50)
    print("실습 완료!")
    print("\n생성된 파일:")
    print("  - family_owlready.owl")


if __name__ == "__main__":
    main()
