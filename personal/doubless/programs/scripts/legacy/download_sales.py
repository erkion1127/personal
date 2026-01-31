#!/usr/bin/env python3
"""
Broj CRM 매출정보 다운로드 프로그램

이 프로그램은 Broj CRM 시스템에서 매출 정보를 자동으로 다운로드하여 SQLite DB에 저장합니다.

주요 기능:
- OAuth 인증 및 JGroup Access Token 획득
- 월별 매출 데이터 조회 (페이징 처리)
- SQLite DB에 자동 저장 (신규 추가/업데이트)
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


class BrojSalesDownloader:
    """Broj CRM 매출정보 다운로더"""

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

        print(f"   설정 로드: ID={config.get('id')}")
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
        # 올바른 API endpoint 사용
        auth_url = f"https://brojserver.broj.co.kr/BroJServer/api/authorization/jgroup?jgroup_key={self.jgroup_key}"

        headers = {
            "Accept": "*/*",
            "Authorization": f"Bearer {self.access_token}",
            "Origin": "https://crm.broj.co.kr",
            "Referer": "https://crm.broj.co.kr/",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
        }

        try:
            response = self.session.get(auth_url, headers=headers)
            response.raise_for_status()
            auth_data = response.json()

            # result 필드에 토큰이 있음
            jgroup_access_token = auth_data.get('result')
            if jgroup_access_token:
                return jgroup_access_token
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

    def download_sales_by_month(self, start_date, end_date):
        """특정 기간의 매출정보 다운로드

        Args:
            start_date: 시작일 (형식: YYYY-MM-DD)
            end_date: 종료일 (형식: YYYY-MM-DD)

        Returns:
            list: 매출 정보 리스트 (lamb_list)
        """
        print(f"\n📅 매출정보 다운로드: {start_date} ~ {end_date}")

        jgroup_access_token = self.get_jgroup_access_token()
        if jgroup_access_token:
            print(f"   JGroup Access Token 획득 성공")

        # 날짜를 밀리초 타임스탬프로 변환
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        end_dt = end_dt.replace(hour=23, minute=59, second=59)

        start_time_ms = int(start_dt.timestamp() * 1000)
        end_time_ms = int(end_dt.timestamp() * 1000)

        all_sales = []
        page_index = 0
        page_size = 100

        api_url = "https://brojserver.broj.co.kr/BroJServer/jgroup/api/reterive/jgproducthistory/jpql"

        while True:
            # JSON payload 생성
            payload_dict = {
                "page": {
                    "page_size": page_size,
                    "page_index": page_index
                },
                "keyword": None,
                "jgroup_key": int(self.jgroup_key),
                "flag_start_time": start_time_ms,
                "flag_finish_time": end_time_ms,
                "sort_properties": "jgp_history_created_dttm",
                "sort_desc": True
            }

            # 중요: search_json_string form field로 전송!
            form_data = {
                "search_json_string": json.dumps(payload_dict, ensure_ascii=False)
            }

            headers = {
                "Accept": "*/*",
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Origin": "https://crm.broj.co.kr",
                "Referer": "https://crm.broj.co.kr/",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
            }

            if jgroup_access_token:
                headers["x-broj-jgroup-access-token"] = jgroup_access_token

            try:
                response = self.session.post(api_url, headers=headers, data=form_data)

                if response.status_code != 200:
                    print(f"   ⚠️  API 호출 실패: {response.status_code}")
                    print(f"   응답: {response.text[:300]}")
                    break

                response.raise_for_status()

                data = response.json()

                if page_index == 0:
                    print(f"   응답 상태: {response.status_code}")
                    print(f"   응답 키: {list(data.keys()) if isinstance(data, dict) else 'List'}")

                # 매출 데이터 추출 (lamb_list에서)
                sales_list = data.get('lamb_list', [])

                if not sales_list:
                    if page_index == 0:
                        print(f"   ⚠️  매출 정보를 찾을 수 없습니다.")
                        print(f"   응답 키: {list(data.keys())}")
                    break

                # 총 개수 확인
                total_count = data.get('lamb_total_count', len(sales_list))
                if page_index == 0:
                    print(f"   총 매출 건수: {total_count}건")

                count = len(sales_list)
                print(f"   페이지 {page_index + 1}: {count}건")

                all_sales.extend(sales_list)

                if count < page_size:
                    break

                page_index += 1

            except requests.exceptions.RequestException as e:
                print(f"❌ 페이지 {page_index + 1} 다운로드 실패: {e}")
                break

        print(f"   ✅ 총 {len(all_sales)}건 다운로드 완료")
        return all_sales

    def save_sales_to_db(self, sales_list, sync_id):
        """매출정보를 DB에 저장"""
        if not sales_list:
            return 0

        cursor = self.conn.cursor()
        insert_count = 0
        update_count = 0

        for sale in sales_list:
            sale_key = sale.get('jgp_history_key')

            if not sale_key:
                continue

            cursor.execute("SELECT jgp_history_key FROM sales WHERE jgp_history_key = ?", (sale_key,))
            exists = cursor.fetchone()

            # 날짜 변환
            created_dttm = ms_to_datetime(sale.get('jgp_history_created_dttm'))
            started_dttm = ms_to_datetime(sale.get('jgp_history_started_dttm'))
            closed_dttm = ms_to_datetime(sale.get('jgp_history_closed_dttm'))

            if exists:
                cursor.execute("""
                    UPDATE sales SET
                        jgp_history_created_dttm = ?,
                        jgp_history_started_dttm = ?,
                        jgp_history_closed_dttm = ?,
                        jgp_history_price = ?,
                        product_origin_price = ?,
                        jgp_history_sale = ?,
                        jgp_history_service = ?,
                        payment_method_type = ?,
                        payment_type = ?,
                        jgp_history_card = ?,
                        jgp_history_money = ?,
                        jgp_history_credit = ?,
                        jgp_history_card_type = ?,
                        jgp_history_installment = ?,
                        jgp_history_product = ?,
                        jgp_history_type = ?,
                        jgp_history_count = ?,
                        jgp_history_day = ?,
                        product_quantity = ?,
                        jgjm_key = ?,
                        jgjm_member_name = ?,
                        jgjm_address = ?,
                        customer_name = ?,
                        trainer_key = ?,
                        trainer_name = ?,
                        status = ?,
                        classification = ?,
                        type = ?,
                        jgp_history_memo = ?,
                        jgp_history_is_refund = ?,
                        package_uuid = ?,
                        sync_id = ?
                    WHERE jgp_history_key = ?
                """, (
                    created_dttm, started_dttm, closed_dttm,
                    sale.get('jgp_history_price'),
                    sale.get('product_origin_price'),
                    sale.get('jgp_history_sale'),
                    sale.get('jgp_history_service'),
                    sale.get('payment_method_type'),
                    sale.get('payment_type'),
                    sale.get('jgp_history_card'),
                    sale.get('jgp_history_money'),
                    sale.get('jgp_history_credit'),
                    sale.get('jgp_history_card_type'),
                    sale.get('jgp_history_installment'),
                    sale.get('jgp_history_product'),
                    sale.get('jgp_history_type'),
                    sale.get('jgp_history_count'),
                    sale.get('jgp_history_day'),
                    sale.get('product_quantity'),
                    sale.get('jgjm_key'),
                    sale.get('jgjm_member_name'),
                    sale.get('jgjm_address'),
                    sale.get('customer_name'),
                    sale.get('trainer_key'),
                    sale.get('trainer_name'),
                    sale.get('status'),
                    sale.get('classification'),
                    sale.get('type'),
                    sale.get('jgp_history_memo'),
                    sale.get('jgp_history_is_refund'),
                    sale.get('package_uuid'),
                    sync_id,
                    sale_key
                ))
                update_count += 1
            else:
                cursor.execute("""
                    INSERT INTO sales (
                        jgp_history_key, jgp_history_created_dttm, jgp_history_started_dttm, jgp_history_closed_dttm,
                        jgp_history_price, product_origin_price, jgp_history_sale, jgp_history_service,
                        payment_method_type, payment_type, jgp_history_card, jgp_history_money, jgp_history_credit,
                        jgp_history_card_type, jgp_history_installment,
                        jgp_history_product, jgp_history_type, jgp_history_count, jgp_history_day, product_quantity,
                        jgjm_key, jgjm_member_name, jgjm_address, customer_name,
                        trainer_key, trainer_name,
                        status, classification, type,
                        jgp_history_memo, jgp_history_is_refund, package_uuid, sync_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sale_key, created_dttm, started_dttm, closed_dttm,
                    sale.get('jgp_history_price'),
                    sale.get('product_origin_price'),
                    sale.get('jgp_history_sale'),
                    sale.get('jgp_history_service'),
                    sale.get('payment_method_type'),
                    sale.get('payment_type'),
                    sale.get('jgp_history_card'),
                    sale.get('jgp_history_money'),
                    sale.get('jgp_history_credit'),
                    sale.get('jgp_history_card_type'),
                    sale.get('jgp_history_installment'),
                    sale.get('jgp_history_product'),
                    sale.get('jgp_history_type'),
                    sale.get('jgp_history_count'),
                    sale.get('jgp_history_day'),
                    sale.get('product_quantity'),
                    sale.get('jgjm_key'),
                    sale.get('jgjm_member_name'),
                    sale.get('jgjm_address'),
                    sale.get('customer_name'),
                    sale.get('trainer_key'),
                    sale.get('trainer_name'),
                    sale.get('status'),
                    sale.get('classification'),
                    sale.get('type'),
                    sale.get('jgp_history_memo'),
                    sale.get('jgp_history_is_refund'),
                    sale.get('package_uuid'),
                    sync_id
                ))
                insert_count += 1

        self.conn.commit()
        print(f"   💾 DB 저장: 신규 {insert_count}건, 업데이트 {update_count}건")
        return insert_count + update_count

    def download_and_save_by_month_range(self, start_month_str, end_month_str):
        """월별로 매출정보 다운로드 및 저장"""
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

            sales_list = self.download_sales_by_month(month_start, month_end)

            if sales_list:
                saved_count = self.save_sales_to_db(sales_list, sync_id)
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
    print("Broj CRM 매출정보 다운로드")
    print("="*80)

    base_dir = Path(__file__).parent.parent
    config_file = base_dir.parent / "config" / "config.yml"
    db_path = base_dir / "data" / "doubless.db"

    downloader = BrojSalesDownloader(config_file, db_path)

    if not downloader.login():
        print("\n❌ 프로그램을 종료합니다.")
        sys.exit(1)

    try:
        downloader.connect_db()

        # 2025년 2월부터 현재까지
        start_month = "2025-02"
        end_month = datetime.now().strftime('%Y-%m')

        print(f"\n📅 조회 기간: {start_month} ~ {end_month}")

        total_count = downloader.download_and_save_by_month_range(start_month, end_month)

        if total_count > 0:
            print(f"\n✅ 모든 매출정보 다운로드 및 저장 완료!")
            print(f"   총 {total_count}건 저장됨")
        else:
            print(f"\n⚠️  매출 데이터를 다운로드하지 못했습니다.")
            print(f"   API 설정을 확인하고 코드를 수정해주세요.")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        downloader.close()


if __name__ == "__main__":
    main()
