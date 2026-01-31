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

        async with httpx.AsyncClient() as client:
            response = await client.post(login_url, headers=headers, content=data)
            response.raise_for_status()

            result = response.json()
            self.access_token = result.get("result", {}).get("access_token")

            if not self.access_token:
                raise Exception("Failed to get access token")

            return True

    async def fetch_members(self, page_size: int = 1000) -> list[dict]:
        """회원 목록 조회"""
        if not self.access_token:
            await self.login()

        all_members = []
        page_index = 0

        async with httpx.AsyncClient() as client:
            while True:
                url = f"{self.base_url}/BroJServer/api/jcustomer/jgroup/{self.jgroup_key}"
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
                members = data.get("result", [])

                if not members:
                    break

                all_members.extend(members)

                if len(members) < page_size:
                    break

                page_index += 1

        return all_members

    async def fetch_lesson_tickets(self, page_size: int = 1000) -> list[dict]:
        """수강권 목록 조회"""
        if not self.access_token:
            await self.login()

        all_tickets = []
        page_index = 0

        async with httpx.AsyncClient() as client:
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
