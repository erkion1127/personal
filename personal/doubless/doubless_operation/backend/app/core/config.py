"""설정 관리"""

from functools import lru_cache
from pathlib import Path
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """애플리케이션 설정"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = "sqlite:///data/operation.db"

    # Broj CRM
    broj_url: str = "https://brojserver.broj.co.kr"
    broj_id: str = ""
    broj_pwd: SecretStr = SecretStr("")
    broj_jgroup_key: str = ""

    # Center Info
    center_name: str = "더블에스"
    center_code: str = "DOUBLESS001"

    # Application
    debug: bool = False

    @property
    def base_dir(self) -> Path:
        """프로젝트 루트 디렉토리"""
        return Path(__file__).parent.parent.parent

    @property
    def data_dir(self) -> Path:
        """데이터 디렉토리"""
        return self.base_dir / "data"

    @property
    def exports_dir(self) -> Path:
        """내보내기 디렉토리"""
        return self.data_dir / "exports"


@lru_cache
def get_settings() -> Settings:
    """설정 싱글톤"""
    return Settings()
