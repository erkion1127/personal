#!/usr/bin/env python3
"""
Broj CRM 매출정보 API 테스트 프로그램
"""

import requests
import json
import yaml
from pathlib import Path
from datetime import datetime
import sys


class BrojSalesAPITester:
    """Broj CRM 매출정보 API 테스터"""

    def __init__(self, config_file):
        """초기화"""
        self.config = self._load_config(config_file)
        self.session = requests.Session()
        self.access_token = None
        self.jgroup_key = None

    def _load_config(self, config_file):
        """설정 파일 로드"""
        with open(config_file, 'r', encoding='utf-8') as f:
            yaml_config = yaml.safe_load(f)

        crm_config = yaml_config.get('broj_crm', {})
        config = {
            'url': crm_config.get('url', ''),
            'id': crm_config.get('id', ''),
            'pwd': crm_config.get('pwd', ''),
            'jgroup_key': str(crm_config.get('jgroup_key', ''))
        }

        print(f"   설정 로드: ID={config.get('id')}")
        return config

    def login(self):
        """로그인 및 토큰 획득"""
        print("🔐 로그인 중...")

        login_url = "https://brojserver.broj.co.kr/BroJServer/joauth/login"

        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept": "*/*",
            "Origin": "https://oauth.broj.co.kr",
            "Referer": "https://oauth.broj.co.kr/",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }

        data = f"member_id={self.config['id']}&member_password={self.config['pwd']}"

        try:
            response = self.session.post(login_url, headers=headers, data=data)
            response.raise_for_status()

            response_data = response.json()
            cookies = response.cookies

            self.access_token = cookies.get('accessToken')
            self.jgroup_key = cookies.get('jgroup_key')

            if not self.access_token:
                if response_data and 'result' in response_data:
                    result = response_data['result']
                    if isinstance(result, dict):
                        self.access_token = result.get('accessToken') or result.get('access_token')

            if not self.access_token:
                print("❌ 로그인 실패")
                return False

            if not self.jgroup_key and 'jgroup_key' in self.config:
                self.jgroup_key = self.config['jgroup_key']

            print("✅ 로그인 성공!")
            print(f"   - Access Token: {self.access_token[:50]}...")
            print(f"   - JGroup Key: {self.jgroup_key}")

            return True

        except Exception as e:
            print(f"❌ 로그인 실패: {e}")
            return False

    def get_jgroup_access_token(self):
        """JGroup Access Token 획득"""
        jgroup_url = f"https://brojserver.broj.co.kr/BroJServer/api/jgroup/{self.jgroup_key}"

        headers = {
            "Accept": "*/*",
            "Authorization": f"Bearer {self.access_token}",
            "Origin": "https://crm.broj.co.kr",
            "Referer": "https://crm.broj.co.kr/",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }

        try:
            response = self.session.get(jgroup_url, headers=headers)
            response.raise_for_status()
            jgroup_data = response.json()

            print(f"\n[DEBUG] JGroup 응답 키: {list(jgroup_data.keys()) if isinstance(jgroup_data, dict) else type(jgroup_data)}")
            print(f"[DEBUG] JGroup 응답 (첫 500자): {json.dumps(jgroup_data, ensure_ascii=False)[:500]}")

            if 'access_token' in jgroup_data:
                return jgroup_data['access_token']
            elif 'result' in jgroup_data and isinstance(jgroup_data['result'], dict):
                if 'access_token' in jgroup_data['result']:
                    return jgroup_data['result']['access_token']
            return None
        except Exception as e:
            print(f"   JGroup Access Token 획득 실패: {e}")
            import traceback
            traceback.print_exc()
            return None

    def test_sales_api(self):
        """매출정보 API 테스트"""
        print("\n📊 매출정보 API 테스트 중...")

        jgroup_access_token = self.get_jgroup_access_token()
        if jgroup_access_token:
            print(f"   JGroup Access Token 획득 성공: {jgroup_access_token[:50]}...")
        else:
            print(f"   ⚠️  JGroup Access Token 획득 실패")

        # 2024년 12월 1일 ~ 12월 31일 (테스트용, 과거 데이터)
        # 2024-12-01 00:00:00 KST = 1733000400000 ms
        # 2024-12-31 23:59:59 KST = 1735660799000 ms
        start_time = 1733000400000
        end_time = 1735660799000

        api_url = "https://brojserver.broj.co.kr/BroJServer/jgroup/api/reterive/jgproducthistory/jpql"

        # 여러 payload 조합 시도
        payloads_to_try = [
            # 1. keyword를 빈 문자열로
            {
                "page": {
                    "page_size": 10,
                    "page_index": 0
                },
                "keyword": "",
                "jgroup_key": int(self.jgroup_key),
                "flag_start_time": start_time,
                "flag_finish_time": end_time,
                "sort_properties": "jgp_history_created_dttm",
                "sort_desc": True
            },
            # 2. keyword 제거
            {
                "page": {
                    "page_size": 10,
                    "page_index": 0
                },
                "jgroup_key": int(self.jgroup_key),
                "flag_start_time": start_time,
                "flag_finish_time": end_time,
                "sort_properties": "jgp_history_created_dttm",
                "sort_desc": True
            }
        ]

        headers = {
            "Accept": "application/json, text/plain, */*",
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json;charset=UTF-8",
            "Origin": "https://crm.broj.co.kr",
            "Referer": "https://crm.broj.co.kr/",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }

        if jgroup_access_token:
            headers["x-broj-jgroup-access-token"] = jgroup_access_token

        for i, payload in enumerate(payloads_to_try, 1):
            print(f"\n{'='*60}")
            print(f"[시도 {i}/{len(payloads_to_try)}]")
            print('='*60)
            print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")

            try:
                response = self.session.post(api_url, json=payload, headers=headers)

                print(f"\n응답 상태 코드: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ 성공!")
                    print(f"응답 키: {list(data.keys()) if isinstance(data, dict) else 'List'}")
                    print(f"\n응답 데이터 (첫 1000자):")
                    print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])

                    # 응답 구조 분석
                    sales_list = None
                    if 'result' in data:
                        if isinstance(data['result'], list):
                            sales_list = data['result']
                        elif isinstance(data['result'], dict):
                            print(f"\nresult 내부 키: {list(data['result'].keys())}")
                            if 'list' in data['result']:
                                sales_list = data['result']['list']
                            elif 'content' in data['result']:
                                sales_list = data['result']['content']
                    elif isinstance(data, list):
                        sales_list = data

                    if sales_list:
                        print(f"\n✅ 매출 데이터 발견: {len(sales_list)}건")
                        if len(sales_list) > 0:
                            print(f"\n첫 번째 매출 데이터 샘플:")
                            print(json.dumps(sales_list[0], indent=2, ensure_ascii=False))

                    return data  # 성공하면 반환

                else:
                    print(f"❌ 실패: {response.status_code}")
                    print(f"응답 본문: {response.text[:300]}")

            except Exception as e:
                print(f"❌ 에러: {e}")

        print("\n⚠️  모든 시도 실패")
        return None


def main():
    """메인 함수"""
    print("="*80)
    print("Broj CRM 매출정보 API 테스트")
    print("="*80)

    base_dir = Path(__file__).parent.parent
    config_file = base_dir.parent / "config" / "config.yml"

    tester = BrojSalesAPITester(config_file)

    if not tester.login():
        print("\n❌ 프로그램을 종료합니다.")
        sys.exit(1)

    tester.test_sales_api()


if __name__ == "__main__":
    main()
