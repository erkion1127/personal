#!/usr/bin/env python3
"""
Broj CRM 출석정보 다운로드 프로그램

이 프로그램은 Broj CRM 시스템에서 출석 정보를 월별로 다운로드하여 SQLite DB에 저장합니다.
"""

import requests
import json
import yaml
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import sys


def ms_to_datetime(ms_timestamp):
    """밀리초 타임스탬프를 datetime 문자열로 변환"""
    if ms_timestamp is None:
        return None
    try:
        dt = datetime.fromtimestamp(ms_timestamp / 1000)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError, OSError):
        return None


class BrojAttendanceDownloader:
    """Broj CRM 출석정보 다운로더"""

    def __init__(self, config_file, db_path):
        """초기화"""
        self.config = self._load_config(config_file)
        self.db_path = Path(db_path)
        self.session = requests.Session()
        self.access_token = None
        self.jgroup_key = None
        self.conn = None

    def _load_config(self, config_file):
        """설정 파일 로드 (YAML 형식)"""
        with open(config_file, 'r', encoding='utf-8') as f:
            yaml_config = yaml.safe_load(f)

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
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
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
                        self.jgroup_key = result.get('jgroupKey') or result.get('jgroup_key')

            if not self.access_token:
                print("❌ 로그인 실패: 토큰을 찾을 수 없습니다.")
                return False

            print("✅ 로그인 성공!")
            print(f"   - Access Token: {self.access_token[:50]}...")

            if not self.jgroup_key and 'jgroup_key' in self.config:
                self.jgroup_key = self.config['jgroup_key']
                print(f"   ✅ 설정에서 JGroup Key 사용: {self.jgroup_key}")

            return True

        except requests.exceptions.RequestException as e:
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
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
        }

        try:
            response = self.session.get(jgroup_url, headers=headers)
            response.raise_for_status()
            jgroup_data = response.json()

            if 'access_token' in jgroup_data:
                return jgroup_data['access_token']
            return None
        except Exception as e:
            print(f"   JGroup Access Token 획득 실패: {e}")
            return None

    def connect_db(self):
        """DB 연결"""
        print(f"📂 DB 연결: {self.db_path}")
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self.conn

    def create_attendance_table(self):
        """출석정보 테이블 생성"""
        print("📋 출석정보 테이블 생성 중...")

        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                jgm_attendance_key INTEGER PRIMARY KEY,
                jgjm_key INTEGER,
                jgjm_member_name TEXT,
                jgjm_member_phone_number TEXT,
                jgjm_member_sex TEXT,
                jgjm_address TEXT,
                attendance_started_dttm TEXT,
                attendance_closed_dttm TEXT,
                attendance_date TEXT,
                attendance_time TEXT,
                temperature REAL,
                status TEXT,
                customer_status TEXT,
                ticket_key INTEGER,
                ticket_name TEXT,
                ticket_type TEXT,
                pass_count INTEGER,
                door_name TEXT,
                member_authority TEXT,
                vaccine_type TEXT,
                vaccine_completed INTEGER,
                sync_id TEXT,
                synced_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY (jgjm_key) REFERENCES members(jgjm_key)
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_attendance_member
            ON attendance(jgjm_key)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_attendance_date
            ON attendance(attendance_date)
        """)

        self.conn.commit()
        print("✅ 출석정보 테이블 생성 완료")

    def download_attendance_by_month(self, start_date, end_date):
        """특정 기간의 출석정보 다운로드"""
        print(f"\n📅 출석정보 다운로드: {start_date} ~ {end_date}")

        jgroup_access_token = self.get_jgroup_access_token()
        if jgroup_access_token:
            print(f"   JGroup Access Token 획득 성공")

        all_attendance = []
        page_index = 0
        page_size = 400

        while True:
            api_url = f"https://brojserver.broj.co.kr/BroJServer/api/jgroup/{self.jgroup_key}/attendance"

            params = {
                "start_date": start_date,
                "close_date": end_date,
                "size": page_size,
                "page_index": page_index,
                "sort_type": "desc"
            }

            headers = {
                "Accept": "*/*",
                "Authorization": f"Bearer {self.access_token}",
                "Origin": "https://crm.broj.co.kr",
                "Referer": "https://crm.broj.co.kr/",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
            }

            if jgroup_access_token:
                headers["x-broj-jgroup-access-token"] = jgroup_access_token

            try:
                response = self.session.get(api_url, params=params, headers=headers)
                response.raise_for_status()

                data = response.json()

                if page_index == 0:
                    print(f"   응답 상태: {response.status_code}")
                    print(f"   응답 키: {list(data.keys()) if isinstance(data, dict) else 'List'}")

                attendance_list = None
                if 'result' in data and isinstance(data['result'], list):
                    attendance_list = data['result']
                elif 'result' in data and isinstance(data['result'], dict):
                    if '_embedded' in data['result'] and 'jgattendances' in data['result']['_embedded']:
                        attendance_list = data['result']['_embedded']['jgattendances']
                elif '_embedded' in data and 'jgattendances' in data['_embedded']:
                    attendance_list = data['_embedded']['jgattendances']
                elif isinstance(data, list):
                    attendance_list = data

                if not attendance_list:
                    if page_index == 0:
                        print(f"   ⚠️  출석 정보를 찾을 수 없습니다.")
                    break

                count = len(attendance_list)
                print(f"   페이지 {page_index + 1}: {count}건")

                all_attendance.extend(attendance_list)

                if count < page_size:
                    break

                page_index += 1

            except requests.exceptions.RequestException as e:
                print(f"❌ 페이지 {page_index + 1} 다운로드 실패: {e}")
                break

        print(f"   ✅ 총 {len(all_attendance)}건 다운로드 완료")
        return all_attendance

    def save_attendance_to_db(self, attendance_list, sync_id):
        """출석정보를 DB에 저장"""
        if not attendance_list:
            return 0

        cursor = self.conn.cursor()
        insert_count = 0
        update_count = 0

        for attendance in attendance_list:
            attendance_key = attendance.get('jgm_attendance_key')

            if not attendance_key:
                continue

            cursor.execute("SELECT jgm_attendance_key FROM attendance WHERE jgm_attendance_key = ?", (attendance_key,))
            exists = cursor.fetchone()

            started_dttm_ms = attendance.get('jgm_attendance_started_dttm')
            started_dttm = ms_to_datetime(started_dttm_ms)

            closed_dttm_ms = attendance.get('jgm_attendance_closed_dttm')
            closed_dttm = ms_to_datetime(closed_dttm_ms)

            attendance_date = None
            attendance_time = None
            if started_dttm:
                try:
                    dt = datetime.strptime(started_dttm, '%Y-%m-%d %H:%M:%S')
                    attendance_date = dt.strftime('%Y-%m-%d')
                    attendance_time = dt.strftime('%H:%M:%S')
                except:
                    pass

            if exists:
                cursor.execute("""
                    UPDATE attendance SET
                        jgjm_key = ?,
                        jgjm_member_name = ?,
                        jgjm_member_phone_number = ?,
                        jgjm_member_sex = ?,
                        jgjm_address = ?,
                        attendance_started_dttm = ?,
                        attendance_closed_dttm = ?,
                        attendance_date = ?,
                        attendance_time = ?,
                        temperature = ?,
                        status = ?,
                        customer_status = ?,
                        ticket_key = ?,
                        ticket_name = ?,
                        ticket_type = ?,
                        pass_count = ?,
                        door_name = ?,
                        member_authority = ?,
                        vaccine_type = ?,
                        vaccine_completed = ?,
                        sync_id = ?
                    WHERE jgm_attendance_key = ?
                """, (
                    attendance.get('jgjm_key'),
                    attendance.get('jgjm_member_name'),
                    attendance.get('jgjm_member_phone_number'),
                    attendance.get('jgjm_member_sex'),
                    attendance.get('jgjm_address'),
                    started_dttm,
                    closed_dttm,
                    attendance_date,
                    attendance_time,
                    attendance.get('temperature'),
                    attendance.get('status'),
                    attendance.get('customer_status'),
                    attendance.get('ticket_key'),
                    attendance.get('ticket_name'),
                    attendance.get('ticket_type'),
                    attendance.get('pass_count'),
                    attendance.get('door_name'),
                    attendance.get('member_authority'),
                    attendance.get('vaccine_type'),
                    attendance.get('vaccine_completed'),
                    sync_id,
                    attendance_key
                ))
                update_count += 1
            else:
                cursor.execute("""
                    INSERT INTO attendance (
                        jgm_attendance_key, jgjm_key, jgjm_member_name, jgjm_member_phone_number,
                        jgjm_member_sex, jgjm_address, attendance_started_dttm, attendance_closed_dttm,
                        attendance_date, attendance_time, temperature, status, customer_status,
                        ticket_key, ticket_name, ticket_type, pass_count, door_name,
                        member_authority, vaccine_type, vaccine_completed, sync_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    attendance_key,
                    attendance.get('jgjm_key'),
                    attendance.get('jgjm_member_name'),
                    attendance.get('jgjm_member_phone_number'),
                    attendance.get('jgjm_member_sex'),
                    attendance.get('jgjm_address'),
                    started_dttm,
                    closed_dttm,
                    attendance_date,
                    attendance_time,
                    attendance.get('temperature'),
                    attendance.get('status'),
                    attendance.get('customer_status'),
                    attendance.get('ticket_key'),
                    attendance.get('ticket_name'),
                    attendance.get('ticket_type'),
                    attendance.get('pass_count'),
                    attendance.get('door_name'),
                    attendance.get('member_authority'),
                    attendance.get('vaccine_type'),
                    attendance.get('vaccine_completed'),
                    sync_id
                ))
                insert_count += 1

        self.conn.commit()
        print(f"   💾 DB 저장: 신규 {insert_count}건, 업데이트 {update_count}건")
        return insert_count + update_count

    def download_and_save_by_month_range(self, start_month_str, end_month_str):
        """월별로 출석정보 다운로드 및 저장"""
        start_date = datetime.strptime(start_month_str, '%Y-%m')
        end_date = datetime.strptime(end_month_str, '%Y-%m')

        sync_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        print(f"\n🔄 동기화 ID: {sync_id}")

        current_date = start_date
        total_count = 0
        month_count = 0

        while current_date <= end_date:
            month_count += 1

            month_start = current_date.strftime('%Y-%m-01')

            next_month = current_date + relativedelta(months=1)
            month_end = (next_month - timedelta(days=1)).strftime('%Y-%m-%d')

            if current_date.year == end_date.year and current_date.month == end_date.month:
                today = datetime.now()
                month_end = today.strftime('%Y-%m-%d')

            print(f"\n{'='*80}")
            print(f"[ {month_count} ] {current_date.strftime('%Y년 %m월')}")
            print('='*80)

            attendance_list = self.download_attendance_by_month(month_start, month_end)

            if attendance_list:
                saved_count = self.save_attendance_to_db(attendance_list, sync_id)
                total_count += saved_count

            current_date = next_month

        print(f"\n{'='*80}")
        print(f"✅ 전체 다운로드 완료")
        print(f"   - 총 {month_count}개월 처리")
        print(f"   - 총 {total_count}건 저장")
        print('='*80)

        return total_count

    def close(self):
        """DB 연결 종료"""
        if self.conn:
            self.conn.close()
            print("✅ DB 연결 종료")


def main():
    """메인 함수"""
    print("="*80)
    print("Broj CRM 출석정보 다운로드")
    print("="*80)

    base_dir = Path(__file__).parent.parent
    config_file = base_dir.parent / "config" / "config.yml"
    db_path = base_dir / "data" / "doubless.db"

    downloader = BrojAttendanceDownloader(config_file, db_path)

    if not downloader.login():
        print("\n❌ 프로그램을 종료합니다.")
        sys.exit(1)

    try:
        downloader.connect_db()
        downloader.create_attendance_table()

        start_month = "2025-02"
        end_month = "2026-01"

        print(f"\n📅 조회 기간: {start_month} ~ {end_month}")

        total_count = downloader.download_and_save_by_month_range(start_month, end_month)

        print(f"\n✅ 모든 출석정보 다운로드 및 저장 완료!")
        print(f"   총 {total_count}건 저장됨")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        downloader.close()


if __name__ == "__main__":
    main()
