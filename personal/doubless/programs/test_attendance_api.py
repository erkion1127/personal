#!/usr/bin/env python3
"""출석정보 API 응답 구조 확인"""

import requests
import json
import yaml
from pathlib import Path

def load_config():
    """설정 파일 로드"""
    base_dir = Path(__file__).parent.parent
    config_file = base_dir.parent / "config" / "config.yml"

    with open(config_file, 'r', encoding='utf-8') as f:
        yaml_config = yaml.safe_load(f)

    crm_config = yaml_config.get('broj_crm', {})
    return {
        'id': crm_config.get('id', ''),
        'pwd': crm_config.get('pwd', ''),
        'jgroup_key': str(crm_config.get('jgroup_key', ''))
    }

def login(config):
    """로그인"""
    session = requests.Session()
    login_url = "https://brojserver.broj.co.kr/BroJServer/joauth/login"

    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Accept": "*/*",
        "User-Agent": "Mozilla/5.0"
    }

    data = f"member_id={config['id']}&member_password={config['pwd']}"

    response = session.post(login_url, headers=headers, data=data)
    response.raise_for_status()

    cookies = response.cookies
    access_token = cookies.get('accessToken')

    if not access_token:
        response_data = response.json()
        if 'result' in response_data:
            result = response_data['result']
            if isinstance(result, dict):
                access_token = result.get('accessToken') or result.get('access_token')

    return session, access_token

def get_jgroup_access_token(session, access_token, jgroup_key):
    """JGroup Access Token 획득"""
    jgroup_url = f"https://brojserver.broj.co.kr/BroJServer/api/jgroup/{jgroup_key}"

    headers = {
        "Accept": "*/*",
        "Authorization": f"Bearer {access_token}",
        "User-Agent": "Mozilla/5.0"
    }

    response = session.get(jgroup_url, headers=headers)
    response.raise_for_status()
    jgroup_data = response.json()

    return jgroup_data.get('access_token')

def test_attendance_api():
    """출석정보 API 테스트"""
    config = load_config()
    session, access_token = login(config)
    jgroup_key = config['jgroup_key']

    print(f"✅ 로그인 성공")
    print(f"JGroup Key: {jgroup_key}")

    jgroup_access_token = get_jgroup_access_token(session, access_token, jgroup_key)
    print(f"✅ JGroup Access Token 획득")

    # 테스트: 2026년 1월 1일부터 3일까지
    api_url = f"https://brojserver.broj.co.kr/BroJServer/api/jgroup/{jgroup_key}/attendance"

    params = {
        "start_date": "2026-01-01",
        "close_date": "2026-01-03",
        "size": 10,
        "page_index": 0,
        "sort_type": "desc"
    }

    headers = {
        "Accept": "*/*",
        "Authorization": f"Bearer {access_token}",
        "x-broj-jgroup-access-token": jgroup_access_token,
        "User-Agent": "Mozilla/5.0"
    }

    response = session.get(api_url, params=params, headers=headers)
    response.raise_for_status()

    data = response.json()

    print("\n" + "="*80)
    print("API 응답 구조")
    print("="*80)
    print(f"응답 키: {list(data.keys())}")

    # result 확인
    if 'result' in data:
        result = data['result']
        print(f"\nresult 타입: {type(result)}")

        if isinstance(result, dict):
            print(f"result 키: {list(result.keys())}")

            # _embedded 확인
            if '_embedded' in result:
                embedded = result['_embedded']
                print(f"_embedded 키: {list(embedded.keys())}")

                # jgattendances 확인
                if 'jgattendances' in embedded:
                    attendances = embedded['jgattendances']
                    print(f"\n출석 데이터 개수: {len(attendances)}개")

                    if attendances:
                        print(f"\n첫 번째 출석 데이터:")
                        print(json.dumps(attendances[0], ensure_ascii=False, indent=2))
        elif isinstance(result, list):
            print(f"result는 리스트: {len(result)}개 항목")
            if result:
                print(f"\n첫 번째 항목:")
                print(json.dumps(result[0], ensure_ascii=False, indent=2))

if __name__ == "__main__":
    test_attendance_api()
