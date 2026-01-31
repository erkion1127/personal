"""Broj CRM API 클라이언트"""

import httpx
from typing import Optional
from app.core.config import get_settings


class BrojClient:
    """Broj CRM API 클라이언트"""

    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.broj_url
        self.access_token: Optional[str] = None
        self.jgroup_access_token: Optional[str] = None
        self.jgroup_key = self.settings.broj_jgroup_key

    async def login(self) -> bool:
        """로그인 및 토큰 획득"""
        login_url = f"{self.base_url}/BroJServer/joauth/login"

        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept": "*/*",
            "Origin": "https://oauth.broj.co.kr",
            "Referer": "https://oauth.broj.co.kr/",
        }

        data = f"member_id={self.settings.broj_id}&member_password={self.settings.broj_pwd.get_secret_value()}"

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(login_url, headers=headers, content=data)
            response.raise_for_status()

            result = response.json()
            self.access_token = result.get("result", {}).get("access_token")

            if not self.access_token:
                raise Exception("Failed to get access token")

            # JGroup Access Token 획득
            await self._get_jgroup_access_token(client)

            return True

    async def _get_jgroup_access_token(self, client: httpx.AsyncClient) -> None:
        """JGroup Access Token 획득"""
        jgroup_url = f"{self.base_url}/BroJServer/api/jgroup/{self.jgroup_key}"

        headers = {
            "Accept": "*/*",
            "Authorization": f"Bearer {self.access_token}",
            "Origin": "https://crm.broj.co.kr",
            "Referer": "https://crm.broj.co.kr/",
        }

        response = await client.get(jgroup_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            self.jgroup_access_token = data.get("access_token")

    async def fetch_members(self, page_size: int = 1000, verbose: bool = True) -> list[dict]:
        """회원 목록 조회"""
        if not self.access_token:
            await self.login()

        all_members = []
        page_index = 0

        async with httpx.AsyncClient(timeout=120) as client:
            while True:
                url = f"{self.base_url}/BroJServer/api/jcustomer/jgroup/{self.jgroup_key}"
                params = {
                    "size": page_size,
                    "page_index": page_index,
                    "status": "ALL",
                    "sort_column": "created_dttm",
                    "sort_type": "desc",
                }
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Accept": "*/*",
                    "Origin": "https://crm.broj.co.kr",
                    "Referer": "https://crm.broj.co.kr/",
                }

                # JGroup Access Token 추가
                if self.jgroup_access_token:
                    headers["x-broj-jgroup-access-token"] = self.jgroup_access_token

                if verbose:
                    print(f"      페이지 {page_index + 1} 요청 중...", flush=True)

                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()

                data = response.json()

                # 응답 형식 확인 (result 배열 또는 _embedded)
                members = None
                if "result" in data and isinstance(data["result"], list):
                    members = data["result"]
                elif "_embedded" in data and "jcustomers" in data["_embedded"]:
                    members = data["_embedded"]["jcustomers"]

                if verbose:
                    count = len(members) if members else 0
                    print(f"      페이지 {page_index + 1}: {count}명 수신", flush=True)

                if not members:
                    break

                all_members.extend(members)

                if len(members) < page_size:
                    if verbose:
                        print("      마지막 페이지입니다.", flush=True)
                    break

                page_index += 1

        return all_members

    async def fetch_lesson_tickets(self, page_size: int = 1000) -> list[dict]:
        """수강권 목록 조회"""
        if not self.access_token:
            await self.login()

        all_tickets = []
        page_index = 0

        async with httpx.AsyncClient(timeout=120) as client:
            while True:
                url = f"{self.base_url}/BroJServer/api/jgroup/lessonticket/{self.jgroup_key}"
                params = {
                    "page_index": page_index,
                    "page_size": page_size,
                }
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Accept": "application/json",
                }

                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()

                data = response.json()
                tickets = data.get("result", [])

                if not tickets:
                    break

                all_tickets.extend(tickets)

                if len(tickets) < page_size:
                    break

                page_index += 1

        return all_tickets
