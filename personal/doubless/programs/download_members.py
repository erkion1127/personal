#!/usr/bin/env python3
"""
Broj CRM 회원정보 다운로드 프로그램

이 프로그램은 Broj CRM 시스템에서 회원 정보를 자동으로 다운로드합니다.
"""

import requests
import json
import yaml
from pathlib import Path
from datetime import datetime
import sys
import shutil

class BrojMemberDownloader:
    """Broj CRM 회원 다운로더"""

    def __init__(self, config_file):
        """초기화"""
        self.config = self._load_config(config_file)
        self.session = requests.Session()
        self.access_token = None
        self.jgroup_key = None
        self.sync_id = None  # 동기화 ID (전체 다운로드에서 공유)
        self.sync_time = None  # 동기화 시작 시간

    def _load_config(self, config_file):
        """설정 파일 로드 (YAML 형식)"""
        with open(config_file, 'r', encoding='utf-8') as f:
            yaml_config = yaml.safe_load(f)

        # broj_crm 섹션에서 설정 추출
        crm_config = yaml_config.get('broj_crm', {})
        config = {
            'url': crm_config.get('url', ''),
            'id': crm_config.get('id', ''),
            'pwd': crm_config.get('pwd', ''),
            'jgroup_key': str(crm_config.get('jgroup_key', ''))
        }

        print(f"   설정 로드: ID={config.get('id')}, PWD={'*' * len(config.get('pwd', ''))}자")
        return config

    def login(self):
        """로그인 및 토큰 획득"""
        print("🔐 로그인 중...")

        login_url = "https://brojserver.broj.co.kr/BroJServer/joauth/login"

        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Origin": "https://oauth.broj.co.kr",
            "Referer": "https://oauth.broj.co.kr/",
            "sec-ch-ua": '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
        }

        # URL 인코딩된 형식으로 데이터 전송
        data = f"member_id={self.config['id']}&member_password={self.config['pwd']}"
        print(f"   요청 데이터: member_id={self.config['id']}&member_password=***")

        try:
            response = self.session.post(login_url, headers=headers, data=data)

            # 디버깅을 위한 응답 출력
            print(f"   상태 코드: {response.status_code}")
            if response.status_code != 200:
                print(f"   응답 내용: {response.text}")

            response.raise_for_status()

            # 응답 확인
            response_data = response.json()
            print(f"   응답 데이터: {json.dumps(response_data, ensure_ascii=False, indent=2)[:500]}")

            # 쿠키에서 토큰 추출
            cookies = response.cookies
            print(f"   쿠키: {dict(cookies)}")

            # Set-Cookie 헤더 확인
            if 'Set-Cookie' in response.headers:
                print(f"   Set-Cookie 헤더: {response.headers['Set-Cookie'][:200]}")

            self.access_token = cookies.get('accessToken')
            self.jgroup_key = cookies.get('jgroup_key')

            # Set-Cookie 헤더에서 직접 파싱
            if not self.jgroup_key and 'Set-Cookie' in response.headers:
                set_cookie_header = response.headers['Set-Cookie']
                if 'jgroup_key=' in set_cookie_header:
                    # jgroup_key 추출
                    import re
                    match = re.search(r'jgroup_key=(\d+)', set_cookie_header)
                    if match:
                        self.jgroup_key = match.group(1)
                        print(f"   Set-Cookie에서 추출한 jgroup_key: {self.jgroup_key}")

            # 응답 본문에서도 토큰 확인
            if response_data and 'result' in response_data:
                result = response_data['result']
                if isinstance(result, dict):
                    if not self.access_token:
                        self.access_token = result.get('accessToken') or result.get('access_token')
                    if not self.jgroup_key:
                        self.jgroup_key = result.get('jgroupKey') or result.get('jgroup_key')

                    # JWT 토큰에서 member_key 추출은 하지 않음 (member_key != jgroup_key)
                    # JGroup 목록 조회로 jgroup_key를 획득해야 함

            if not self.access_token:
                print("❌ 로그인 실패: 토큰을 찾을 수 없습니다.")
                print(f"   Access Token: {self.access_token}")
                print(f"   JGroup Key: {self.jgroup_key}")
                return False

            print("✅ 로그인 성공!")
            print(f"   - Access Token: {self.access_token[:50]}...")
            print(f"   - JGroup Key: {self.jgroup_key}")

            # JGroup Key가 없으면 설정에서 가져오기
            if not self.jgroup_key and 'jgroup_key' in self.config:
                self.jgroup_key = self.config['jgroup_key']
                print(f"   ✅ 설정에서 JGroup Key 사용: {self.jgroup_key}")

            # 여전히 없으면 jgroup 목록 조회
            if not self.jgroup_key:
                print("\n📋 JGroup 목록 조회 중...")
                self.jgroup_key = self._get_jgroup_list()
                if self.jgroup_key:
                    print(f"   ✅ JGroup Key 획득: {self.jgroup_key}")

            return True

        except requests.exceptions.RequestException as e:
            print(f"❌ 로그인 실패: {e}")
            return False

    def _get_jgroup_list(self):
        """사용자의 JGroup 목록 조회"""
        jgroup_list_url = "https://brojserver.broj.co.kr/BroJServer/api/jgroup"

        headers = {
            "Accept": "*/*",
            "Authorization": f"Bearer {self.access_token}",
            "Origin": "https://crm.broj.co.kr",
            "Referer": "https://crm.broj.co.kr/",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
        }

        try:
            response = self.session.get(jgroup_list_url, headers=headers)
            response.raise_for_status()
            jgroup_data = response.json()

            print(f"   JGroup 응답: {json.dumps(jgroup_data, ensure_ascii=False, indent=2)[:500]}")

            # 첫 번째 jgroup의 key 사용
            if '_embedded' in jgroup_data and 'jgroups' in jgroup_data['_embedded']:
                jgroups = jgroup_data['_embedded']['jgroups']
                if jgroups and len(jgroups) > 0:
                    return str(jgroups[0].get('jgroup_key'))
            elif isinstance(jgroup_data, list) and len(jgroup_data) > 0:
                return str(jgroup_data[0].get('jgroup_key'))

            return None
        except Exception as e:
            print(f"   JGroup 목록 조회 실패: {e}")
            return None

    def get_jgroup_access_token(self):
        """JGroup Access Token 획득"""
        # 먼저 jgroup 정보를 가져와야 함
        jgroup_url = f"https://brojserver.broj.co.kr/BroJServer/api/jgroup/{self.jgroup_key}"

        headers = {
            "Accept": "*/*",
            "Authorization": f"Bearer {self.access_token}",
            "Origin": "https://crm.broj.co.kr",
            "Referer": "https://crm.broj.co.kr/",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
        }

        try:
            response = self.session.get(jgroup_url, headers=headers)
            response.raise_for_status()
            jgroup_data = response.json()

            # jgroup access token 추출
            if 'access_token' in jgroup_data:
                return jgroup_data['access_token']
            return None
        except Exception as e:
            print(f"   JGroup Access Token 획득 실패: {e}")
            return None

    def download_lesson_tickets(self, output_dir):
        """수강권 정보 다운로드 (페이징 처리)"""
        print("\n📚 수강권 정보 다운로드 중...")

        # JGroup Access Token 획득
        jgroup_access_token = self.get_jgroup_access_token()
        if jgroup_access_token:
            print(f"   JGroup Access Token 획득 성공: {jgroup_access_token[:30]}...")

        # 동기화 정보 (main에서 설정된 값 사용)
        sync_time = self.sync_time if self.sync_time else datetime.now()
        sync_id = self.sync_id if self.sync_id else sync_time.strftime('%Y%m%d_%H%M%S')

        all_lesson_tickets = []
        page_index = 0
        page_size = 1000

        while True:
            print(f"\n   📄 페이지 {page_index + 1} 다운로드 중...")

            # API URL 구성 (수강권)
            api_url = f"https://brojserver.broj.co.kr/BroJServer/api/jgroup/lessonticket/{self.jgroup_key}"

            params = {
                "size": page_size,
                "page_index": page_index,
                "status": "ALL",
                "keyword": "",
                "sort_type": "desc",
                "sort_column": "created_dttm"
            }

            headers = {
                "Accept": "*/*",
                "Authorization": f"Bearer {self.access_token}",
                "Origin": "https://crm.broj.co.kr",
                "Referer": "https://crm.broj.co.kr/",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
            }

            # x-broj-jgroup-access-token 헤더 추가
            if jgroup_access_token:
                headers["x-broj-jgroup-access-token"] = jgroup_access_token

            try:
                response = self.session.get(api_url, params=params, headers=headers)
                response.raise_for_status()

                data = response.json()

                # 응답 디버깅 (첫 페이지만)
                if page_index == 0:
                    print(f"   응답 상태: {response.status_code}")
                    print(f"   응답 키: {list(data.keys()) if isinstance(data, dict) else 'List'}")
                    print(f"   응답 데이터 (처음 500자): {json.dumps(data, ensure_ascii=False)[:500]}")

                # 수강권 수 확인
                lesson_tickets = None
                if 'result' in data and isinstance(data['result'], dict):
                    # result 내부의 배열 찾기
                    if '_embedded' in data['result'] and 'jlessontickets' in data['result']['_embedded']:
                        lesson_tickets = data['result']['_embedded']['jlessontickets']
                elif 'result' in data and isinstance(data['result'], list):
                    lesson_tickets = data['result']
                elif '_embedded' in data and 'jlessontickets' in data['_embedded']:
                    lesson_tickets = data['_embedded']['jlessontickets']
                elif isinstance(data, list):
                    lesson_tickets = data

                if not lesson_tickets:
                    print(f"   ⚠️  페이지 {page_index + 1}에서 수강권 정보를 찾을 수 없습니다.")
                    break

                ticket_count = len(lesson_tickets)
                print(f"   ✅ 페이지 {page_index + 1}: {ticket_count}건")

                all_lesson_tickets.extend(lesson_tickets)

                # 마지막 페이지인지 확인
                if ticket_count < page_size:
                    print(f"   📋 마지막 페이지입니다.")
                    break

                page_index += 1

            except requests.exceptions.RequestException as e:
                print(f"❌ 페이지 {page_index + 1} 다운로드 실패: {e}")
                break

        if all_lesson_tickets:
            total_count = len(all_lesson_tickets)
            print(f"\n✅ 전체 수강권 정보 다운로드 완료: {total_count}건 ({page_index + 1}페이지)")

            # 메타데이터 포함하여 저장
            result_data = {
                "sync_info": {
                    "sync_id": sync_id,
                    "sync_time": sync_time.isoformat(),
                    "sync_time_kr": sync_time.strftime('%Y년 %m월 %d일 %H시 %M분 %S초'),
                    "total_lesson_tickets": total_count,
                    "total_pages": page_index + 1,
                    "page_size": page_size
                },
                "lesson_tickets": all_lesson_tickets
            }

            # 파일 저장
            output_file = output_dir / f"lesson_tickets_sync_{sync_id}.json"

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)

            print(f"💾 저장 완료: {output_file}")

            # 간단한 통계 출력
            self._print_lesson_ticket_summary(all_lesson_tickets)

            return output_file
        else:
            print("⚠️  수강권 정보를 찾을 수 없습니다.")
            return None

    def download_tickets(self, output_dir):
        """회원권 정보 다운로드 (페이징 처리)"""
        print("\n🎫 회원권 정보 다운로드 중...")

        # JGroup Access Token 획득
        jgroup_access_token = self.get_jgroup_access_token()
        if jgroup_access_token:
            print(f"   JGroup Access Token 획득 성공: {jgroup_access_token[:30]}...")

        # 동기화 정보 (main에서 설정된 값 사용)
        sync_time = self.sync_time if self.sync_time else datetime.now()
        sync_id = self.sync_id if self.sync_id else sync_time.strftime('%Y%m%d_%H%M%S')

        all_tickets = []
        page_index = 0
        page_size = 1000

        while True:
            print(f"\n   📄 페이지 {page_index + 1} 다운로드 중...")

            # API URL 구성 (회원권)
            # 예: https://brojserver.broj.co.kr/BroJServer/jgroup/ticketdetails/533109104
            api_url = f"https://brojserver.broj.co.kr/BroJServer/jgroup/ticketdetails/{self.jgroup_key}"

            # URL 인코딩된 시간 문자열 생성
            # 예: Fri Dec 26 2025 00:57:58 GMT+0900 (한국 표준시)
            time_str = sync_time.strftime('%a %b %d %Y %H:%M:%S GMT+0900 (한국 표준시)')

            params = {
                "jtd_standard_time": time_str,
                "page_index": page_index,
                "jtd_expired_day": 10,
                "status": "all",
                "page_size": page_size
            }

            headers = {
                "Accept": "*/*",
                "Authorization": f"Bearer {self.access_token}",
                "Origin": "https://crm.broj.co.kr",
                "Referer": "https://crm.broj.co.kr/",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
            }

            # x-broj-jgroup-access-token 헤더 추가
            if jgroup_access_token:
                headers["x-broj-jgroup-access-token"] = jgroup_access_token

            try:
                response = self.session.get(api_url, params=params, headers=headers)
                response.raise_for_status()

                data = response.json()

                # 응답 디버깅 (첫 페이지만)
                if page_index == 0:
                    print(f"   응답 상태: {response.status_code}")
                    print(f"   응답 키: {list(data.keys()) if isinstance(data, dict) else 'List'}")
                    print(f"   응답 데이터 (처음 500자): {json.dumps(data, ensure_ascii=False)[:500]}")

                # 회원권 수 확인
                tickets = None
                if 'result' in data and isinstance(data['result'], dict):
                    # result.gospel 배열에 데이터가 있는 경우
                    if 'gospel' in data['result'] and isinstance(data['result']['gospel'], list):
                        tickets = data['result']['gospel']
                elif 'result' in data and isinstance(data['result'], list):
                    tickets = data['result']
                elif '_embedded' in data and 'jtickets' in data['_embedded']:
                    tickets = data['_embedded']['jtickets']
                elif isinstance(data, list):
                    tickets = data

                if not tickets:
                    print(f"   ⚠️  페이지 {page_index + 1}에서 회원권 정보를 찾을 수 없습니다.")
                    break

                ticket_count = len(tickets)
                print(f"   ✅ 페이지 {page_index + 1}: {ticket_count}건")

                all_tickets.extend(tickets)

                # 마지막 페이지인지 확인
                if ticket_count < page_size:
                    print(f"   📋 마지막 페이지입니다.")
                    break

                page_index += 1

            except requests.exceptions.RequestException as e:
                print(f"❌ 페이지 {page_index + 1} 다운로드 실패: {e}")
                break

        if all_tickets:
            total_count = len(all_tickets)
            print(f"\n✅ 전체 회원권 정보 다운로드 완료: {total_count}건 ({page_index + 1}페이지)")

            # 메타데이터 포함하여 저장
            result_data = {
                "sync_info": {
                    "sync_id": sync_id,
                    "sync_time": sync_time.isoformat(),
                    "sync_time_kr": sync_time.strftime('%Y년 %m월 %d일 %H시 %M분 %S초'),
                    "total_tickets": total_count,
                    "total_pages": page_index + 1,
                    "page_size": page_size
                },
                "tickets": all_tickets
            }

            # 파일 저장
            output_file = output_dir / f"tickets_sync_{sync_id}.json"

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)

            print(f"💾 저장 완료: {output_file}")

            # 간단한 통계 출력
            self._print_ticket_summary(all_tickets)

            return output_file
        else:
            print("⚠️  회원권 정보를 찾을 수 없습니다.")
            return None

    def download_members(self, output_dir):
        """회원 정보 다운로드 (페이징 처리)"""
        print("\n📥 회원 정보 다운로드 중...")

        # JGroup Access Token 획득
        jgroup_access_token = self.get_jgroup_access_token()
        if jgroup_access_token:
            print(f"   JGroup Access Token 획득 성공: {jgroup_access_token[:30]}...")

        # 동기화 정보 (main에서 설정된 값 사용)
        sync_time = self.sync_time if self.sync_time else datetime.now()
        sync_id = self.sync_id if self.sync_id else sync_time.strftime('%Y%m%d_%H%M%S')

        all_members = []
        page_index = 0
        page_size = 1000

        while True:
            print(f"\n   📄 페이지 {page_index + 1} 다운로드 중...")

            # API URL 구성
            api_url = f"https://brojserver.broj.co.kr/BroJServer/api/jcustomer/jgroup/{self.jgroup_key}"

            params = {
                "size": page_size,
                "page_index": page_index,
                "status": "ALL",
                "sort_column": "created_dttm",
                "sort_type": "desc"
            }

            headers = {
                "Accept": "*/*",
                "Authorization": f"Bearer {self.access_token}",
                "Origin": "https://crm.broj.co.kr",
                "Referer": "https://crm.broj.co.kr/",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
            }

            # x-broj-jgroup-access-token 헤더 추가
            if jgroup_access_token:
                headers["x-broj-jgroup-access-token"] = jgroup_access_token

            try:
                response = self.session.get(api_url, params=params, headers=headers)
                response.raise_for_status()

                data = response.json()

                # 회원 수 확인
                members = None
                if 'result' in data and isinstance(data['result'], list):
                    members = data['result']
                elif '_embedded' in data and 'jcustomers' in data['_embedded']:
                    members = data['_embedded']['jcustomers']

                if not members:
                    print(f"   ⚠️  페이지 {page_index + 1}에서 회원 정보를 찾을 수 없습니다.")
                    break

                member_count = len(members)
                print(f"   ✅ 페이지 {page_index + 1}: {member_count}명")

                all_members.extend(members)

                # 마지막 페이지인지 확인 (가져온 회원 수가 page_size보다 작으면 마지막)
                if member_count < page_size:
                    print(f"   📋 마지막 페이지입니다.")
                    break

                page_index += 1

            except requests.exceptions.RequestException as e:
                print(f"❌ 페이지 {page_index + 1} 다운로드 실패: {e}")
                break

        if all_members:
            total_count = len(all_members)
            print(f"\n✅ 전체 회원 정보 다운로드 완료: {total_count}명 ({page_index + 1}페이지)")

            # 메타데이터 포함하여 저장
            result_data = {
                "sync_info": {
                    "sync_id": sync_id,
                    "sync_time": sync_time.isoformat(),
                    "sync_time_kr": sync_time.strftime('%Y년 %m월 %d일 %H시 %M분 %S초'),
                    "total_members": total_count,
                    "total_pages": page_index + 1,
                    "page_size": page_size
                },
                "members": all_members
            }

            # 파일 저장
            output_file = output_dir / f"members_sync_{sync_id}.json"

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)

            print(f"💾 저장 완료: {output_file}")

            # 간단한 통계 출력
            self._print_summary(all_members)

            return output_file
        else:
            print("⚠️  회원 정보를 찾을 수 없습니다.")
            return None

    def _print_summary(self, members):
        """회원 통계 출력"""
        print("\n📊 회원 통계:")
        print(f"   - 총 회원 수: {len(members)}명")

        # 상태별 통계
        status_count = {}
        for member in members:
            status = member.get('status', member.get('classification', 'UNKNOWN'))
            status_count[status] = status_count.get(status, 0) + 1

        print("   - 상태별 현황:")
        for status, count in sorted(status_count.items()):
            print(f"      • {status}: {count}명")

    def _print_ticket_summary(self, tickets):
        """회원권 통계 출력"""
        print("\n📊 회원권 통계:")
        print(f"   - 총 회원권 수: {len(tickets)}건")

        # 상태별 통계
        status_count = {}
        for ticket in tickets:
            status = ticket.get('status', ticket.get('jtd_status', 'UNKNOWN'))
            status_count[status] = status_count.get(status, 0) + 1

        print("   - 상태별 현황:")
        for status, count in sorted(status_count.items()):
            print(f"      • {status}: {count}건")

    def _print_lesson_ticket_summary(self, lesson_tickets):
        """수강권 통계 출력"""
        print("\n📊 수강권 통계:")
        print(f"   - 총 수강권 수: {len(lesson_tickets)}건")

        # 상태별 통계
        status_count = {}
        for ticket in lesson_tickets:
            status = ticket.get('status', ticket.get('jlt_status', 'UNKNOWN'))
            status_count[status] = status_count.get(status, 0) + 1

        print("   - 상태별 현황:")
        for status, count in sorted(status_count.items()):
            print(f"      • {status}: {count}건")


def main():
    """메인 함수"""
    print("="*80)
    print("Broj CRM 데이터 다운로드")
    print("="*80)

    # 경로 설정
    base_dir = Path(__file__).parent.parent
    config_file = base_dir.parent / "config" / "config.yml"
    sync_base_dir = base_dir / "회원관리" / "동기화"

    # 동기화 기본 디렉토리 생성
    sync_base_dir.mkdir(parents=True, exist_ok=True)

    # 다운로더 생성
    downloader = BrojMemberDownloader(config_file)

    # 로그인
    if not downloader.login():
        print("\n❌ 프로그램을 종료합니다.")
        sys.exit(1)

    # 동기화 ID 및 시간 설정 (전체 다운로드에서 공유)
    sync_time = datetime.now()
    sync_id = sync_time.strftime('%Y%m%d_%H%M%S')
    downloader.sync_id = sync_id
    downloader.sync_time = sync_time

    # 이번 동기화를 위한 폴더 생성
    sync_dir = sync_base_dir / sync_id
    sync_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n📁 동기화 폴더 생성: {sync_dir.name}")
    print(f"   동기화 ID: {sync_id}")
    print(f"   동기화 시간: {sync_time.strftime('%Y년 %m월 %d일 %H시 %M분 %S초')}")

    # 성공/실패 카운트
    success_count = 0
    total_count = 3
    downloaded_files = {}

    # 1. 회원 정보 다운로드
    print("\n" + "="*80)
    print("[ 1/3 ] 회원 정보 다운로드")
    print("="*80)
    members_file = downloader.download_members(sync_dir)
    if members_file:
        success_count += 1
        downloaded_files['members'] = members_file
        print(f"✅ 회원 정보 저장: {members_file.name}")
    else:
        print("❌ 회원 정보 다운로드 실패")

    # 2. 회원권 정보 다운로드
    print("\n" + "="*80)
    print("[ 2/3 ] 회원권 정보 다운로드")
    print("="*80)
    tickets_file = downloader.download_tickets(sync_dir)
    if tickets_file:
        success_count += 1
        downloaded_files['tickets'] = tickets_file
        print(f"✅ 회원권 정보 저장: {tickets_file.name}")
    else:
        print("❌ 회원권 정보 다운로드 실패")

    # 3. 수강권 정보 다운로드
    print("\n" + "="*80)
    print("[ 3/3 ] 수강권 정보 다운로드")
    print("="*80)
    lesson_tickets_file = downloader.download_lesson_tickets(sync_dir)
    if lesson_tickets_file:
        success_count += 1
        downloaded_files['lesson_tickets'] = lesson_tickets_file
        print(f"✅ 수강권 정보 저장: {lesson_tickets_file.name}")
    else:
        print("❌ 수강권 정보 다운로드 실패")

    # 동기화 완료 후 처리
    if success_count == total_count:
        print("\n" + "="*80)
        print("동기화 후처리")
        print("="*80)

        # 1. sync_info.json 생성
        sync_info = {
            "sync_id": sync_id,
            "sync_time": sync_time.isoformat(),
            "sync_time_kr": sync_time.strftime('%Y년 %m월 %d일 %H시 %M분 %S초'),
            "success": True,
            "files": {
                "members": members_file.name if members_file else None,
                "tickets": tickets_file.name if tickets_file else None,
                "lesson_tickets": lesson_tickets_file.name if lesson_tickets_file else None
            }
        }

        sync_info_file = sync_dir / "sync_info.json"
        with open(sync_info_file, 'w', encoding='utf-8') as f:
            json.dump(sync_info, f, ensure_ascii=False, indent=2)
        print(f"📄 동기화 정보 저장: {sync_info_file.name}")

        # 2. latest 폴더 업데이트
        latest_dir = sync_base_dir / "latest"
        if latest_dir.exists():
            shutil.rmtree(latest_dir)
        latest_dir.mkdir(parents=True, exist_ok=True)

        # 파일 복사
        for file_type, file_path in downloaded_files.items():
            if file_path:
                dest = latest_dir / file_path.name
                shutil.copy2(file_path, dest)
                print(f"📋 Latest 복사: {file_path.name}")

        # sync_info도 복사
        shutil.copy2(sync_info_file, latest_dir / "sync_info.json")
        print(f"✅ Latest 폴더 업데이트 완료")

        # 3. sync_history.json 업데이트
        history_file = sync_base_dir / "sync_history.json"
        history = []

        if history_file.exists():
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)

        # 각 파일의 레코드 수 읽기
        record_counts = {}
        for file_type, file_path in downloaded_files.items():
            if file_path:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'sync_info' in data:
                        if 'total_members' in data['sync_info']:
                            record_counts['members'] = data['sync_info']['total_members']
                        elif 'total_tickets' in data['sync_info']:
                            record_counts['tickets'] = data['sync_info']['total_tickets']
                        elif 'total_lesson_tickets' in data['sync_info']:
                            record_counts['lesson_tickets'] = data['sync_info']['total_lesson_tickets']

        history_entry = {
            "sync_id": sync_id,
            "sync_time": sync_time.isoformat(),
            "sync_time_kr": sync_time.strftime('%Y년 %m월 %d일 %H시 %M분 %S초'),
            "success": True,
            "record_counts": record_counts,
            "files": list(downloaded_files.keys())
        }

        history.append(history_entry)

        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        print(f"📜 동기화 이력 업데이트: {history_file.name}")

    # 최종 결과
    print("\n" + "="*80)
    print("다운로드 완료")
    print("="*80)
    print(f"성공: {success_count}/{total_count}")
    print(f"동기화 폴더: {sync_dir}")

    if success_count < total_count:
        print("\n⚠️  일부 다운로드가 실패했습니다.")
        sys.exit(1)
    else:
        print("\n✅ 모든 데이터 동기화 완료!")
        print(f"   최신 데이터: {sync_base_dir / 'latest'}")
        sys.exit(0)


if __name__ == "__main__":
    main()
