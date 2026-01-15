"""날짜/시간 변환 유틸리티

Broj CRM API는 밀리초 타임스탬프를 사용하므로,
datetime 문자열과 밀리초 타임스탬프 간 변환이 필요합니다.

Legacy 참조:
- programs/scripts/legacy/sync_to_db.py (L16-25)
- programs/scripts/legacy/download_sales.py (L21-29)
"""

from datetime import datetime
from typing import Optional


def ms_to_datetime(ms_timestamp: Optional[int]) -> Optional[str]:
    """밀리초 타임스탬프를 datetime 문자열로 변환

    Broj CRM API는 밀리초 단위 Unix 타임스탬프를 사용합니다.
    이를 'YYYY-MM-DD HH:MM:SS' 형식의 문자열로 변환합니다.

    Args:
        ms_timestamp: 밀리초 단위 Unix 타임스탬프

    Returns:
        'YYYY-MM-DD HH:MM:SS' 형식의 문자열, 입력이 None이면 None 반환

    Examples:
        >>> ms_to_datetime(1735660799000)
        '2024-12-31 23:59:59'

        >>> ms_to_datetime(None)
        None

        >>> ms_to_datetime(1733000400000)
        '2024-12-01 00:00:00'
    """
    if ms_timestamp is None:
        return None

    try:
        # 밀리초를 초로 변환하여 datetime 생성
        dt = datetime.fromtimestamp(ms_timestamp / 1000)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError, OSError):
        # 잘못된 타임스탬프 값이거나 범위를 벗어난 경우
        return None


def datetime_to_ms(dt_string: str) -> int:
    """datetime 문자열을 밀리초 타임스탬프로 변환

    'YYYY-MM-DD HH:MM:SS' 형식의 문자열을 밀리초 단위 Unix 타임스탬프로 변환합니다.
    Broj CRM API 호출시 날짜 범위를 지정할 때 사용됩니다.

    Args:
        dt_string: 'YYYY-MM-DD HH:MM:SS' 형식의 datetime 문자열

    Returns:
        밀리초 단위 Unix 타임스탬프

    Raises:
        ValueError: 잘못된 datetime 형식

    Examples:
        >>> datetime_to_ms('2024-12-31 23:59:59')
        1735660799000

        >>> datetime_to_ms('2024-12-01 00:00:00')
        1733000400000
    """
    dt = datetime.strptime(dt_string, '%Y-%m-%d %H:%M:%S')
    return int(dt.timestamp() * 1000)


def get_current_timestamp() -> str:
    """현재 시간을 datetime 문자열로 반환

    현재 로컬 시간을 'YYYY-MM-DD HH:MM:SS' 형식으로 반환합니다.
    동기화 ID, 로그 타임스탬프 등에 사용됩니다.

    Returns:
        현재 시간의 'YYYY-MM-DD HH:MM:SS' 형식 문자열

    Examples:
        >>> timestamp = get_current_timestamp()
        >>> len(timestamp)
        19
    """
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def parse_date(date_string: str, format: str = '%Y-%m-%d') -> datetime:
    """날짜 문자열을 datetime 객체로 파싱

    다양한 형식의 날짜 문자열을 datetime 객체로 변환합니다.

    Args:
        date_string: 날짜 문자열
        format: 날짜 형식 (기본값: '%Y-%m-%d')

    Returns:
        datetime 객체

    Raises:
        ValueError: 잘못된 날짜 형식

    Examples:
        >>> dt = parse_date('2024-12-31')
        >>> dt.year
        2024

        >>> dt = parse_date('31/12/2024', '%d/%m/%Y')
        >>> dt.month
        12
    """
    return datetime.strptime(date_string, format)


def format_date(dt: datetime, format: str = '%Y-%m-%d') -> str:
    """datetime 객체를 지정된 형식의 문자열로 변환

    Args:
        dt: datetime 객체
        format: 출력 형식 (기본값: '%Y-%m-%d')

    Returns:
        형식화된 날짜 문자열

    Examples:
        >>> from datetime import datetime
        >>> dt = datetime(2024, 12, 31, 23, 59, 59)
        >>> format_date(dt)
        '2024-12-31'

        >>> format_date(dt, '%Y년 %m월 %d일')
        '2024년 12월 31일'
    """
    return dt.strftime(format)
