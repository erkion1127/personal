"""date_utils 모듈 테스트

날짜/시간 변환 함수들의 정확성을 검증합니다.
"""

import pytest
from datetime import datetime
from backend.utils.date_utils import (
    ms_to_datetime,
    datetime_to_ms,
    get_current_timestamp,
    parse_date,
    format_date
)


class TestMsToDatetime:
    """ms_to_datetime 함수 테스트"""

    def test_valid_timestamp(self):
        """정상적인 타임스탬프 변환"""
        # 2024-12-31 23:59:59 KST (대략)
        result = ms_to_datetime(1735660799000)
        assert result is not None
        assert isinstance(result, str)
        assert len(result) == 19  # 'YYYY-MM-DD HH:MM:SS' 길이

    def test_none_input(self):
        """None 입력시 None 반환"""
        assert ms_to_datetime(None) is None

    def test_zero_timestamp(self):
        """0 타임스탬프 (1970-01-01 00:00:00 UTC)"""
        result = ms_to_datetime(0)
        assert result is not None
        assert '1970-01-01' in result

    def test_negative_timestamp(self):
        """음수 타임스탬프 처리"""
        # 1970년 이전 날짜 (시스템에 따라 다를 수 있음)
        result = ms_to_datetime(-1000)
        # None 반환하거나 유효한 날짜 반환
        assert result is None or isinstance(result, str)

    def test_recent_timestamp(self):
        """최근 타임스탬프 (2025-01-01)"""
        # 2025-01-01 00:00:00 KST
        result = ms_to_datetime(1735660800000)
        assert result is not None
        assert '2025' in result


class TestDatetimeToMs:
    """datetime_to_ms 함수 테스트"""

    def test_valid_datetime_string(self):
        """정상적인 datetime 문자열 변환"""
        result = datetime_to_ms('2024-12-31 23:59:59')
        assert isinstance(result, int)
        assert result > 0

    def test_specific_datetime(self):
        """특정 datetime 변환 및 역변환 검증"""
        original = '2024-01-01 12:00:00'
        ms = datetime_to_ms(original)
        converted_back = ms_to_datetime(ms)
        assert converted_back == original

    def test_invalid_format(self):
        """잘못된 형식의 문자열"""
        with pytest.raises(ValueError):
            datetime_to_ms('2024/12/31')

    def test_invalid_date(self):
        """존재하지 않는 날짜"""
        with pytest.raises(ValueError):
            datetime_to_ms('2024-13-01 00:00:00')  # 13월

    def test_roundtrip_conversion(self):
        """왕복 변환 테스트 (ms -> datetime -> ms)"""
        original_ms = 1735660799000
        dt_string = ms_to_datetime(original_ms)
        converted_ms = datetime_to_ms(dt_string)
        # 밀리초 단위까지 일치해야 함
        assert converted_ms == original_ms


class TestGetCurrentTimestamp:
    """get_current_timestamp 함수 테스트"""

    def test_returns_string(self):
        """문자열 반환 확인"""
        result = get_current_timestamp()
        assert isinstance(result, str)

    def test_correct_format(self):
        """올바른 형식 확인"""
        result = get_current_timestamp()
        assert len(result) == 19  # 'YYYY-MM-DD HH:MM:SS'
        # 형식 검증: 파싱 가능해야 함
        dt = datetime.strptime(result, '%Y-%m-%d %H:%M:%S')
        assert dt is not None

    def test_current_time(self):
        """현재 시간과 근접한지 확인"""
        before = datetime.now()
        timestamp_str = get_current_timestamp()
        after = datetime.now()

        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')

        # 테스트 실행 시간 고려 (1초 이내)
        assert before <= timestamp <= after + datetime.resolution


class TestParseDate:
    """parse_date 함수 테스트"""

    def test_default_format(self):
        """기본 형식 (YYYY-MM-DD) 파싱"""
        result = parse_date('2024-12-31')
        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 12
        assert result.day == 31

    def test_custom_format(self):
        """커스텀 형식 파싱"""
        result = parse_date('31/12/2024', '%d/%m/%Y')
        assert result.year == 2024
        assert result.month == 12
        assert result.day == 31

    def test_invalid_date(self):
        """잘못된 날짜"""
        with pytest.raises(ValueError):
            parse_date('2024-02-30')  # 2월 30일은 없음

    def test_invalid_format(self):
        """형식 불일치"""
        with pytest.raises(ValueError):
            parse_date('2024/12/31', '%Y-%m-%d')


class TestFormatDate:
    """format_date 함수 테스트"""

    def test_default_format(self):
        """기본 형식 (YYYY-MM-DD) 출력"""
        dt = datetime(2024, 12, 31, 23, 59, 59)
        result = format_date(dt)
        assert result == '2024-12-31'

    def test_custom_format(self):
        """커스텀 형식 출력"""
        dt = datetime(2024, 12, 31, 23, 59, 59)
        result = format_date(dt, '%Y년 %m월 %d일')
        assert result == '2024년 12월 31일'

    def test_time_included(self):
        """시간 포함 형식"""
        dt = datetime(2024, 12, 31, 23, 59, 59)
        result = format_date(dt, '%Y-%m-%d %H:%M:%S')
        assert result == '2024-12-31 23:59:59'


class TestIntegration:
    """통합 테스트"""

    def test_full_workflow(self):
        """전체 워크플로우 테스트: ms -> datetime -> parse -> format -> ms"""
        # 1. 밀리초 타임스탬프 -> datetime 문자열
        original_ms = 1735660799000
        dt_string = ms_to_datetime(original_ms)

        # 2. datetime 문자열 -> datetime 객체
        dt_obj = parse_date(dt_string[:10])  # 날짜 부분만

        # 3. datetime 객체 -> 형식화된 문자열
        formatted = format_date(dt_obj)
        assert len(formatted) == 10  # 'YYYY-MM-DD'

        # 4. 원본 datetime 문자열 -> 밀리초
        converted_ms = datetime_to_ms(dt_string)
        assert converted_ms == original_ms

    def test_boundary_values(self):
        """경계값 테스트"""
        # Unix epoch
        assert ms_to_datetime(0) is not None

        # 먼 미래 (2099-12-31)
        future_ms = 4102444799000
        result = ms_to_datetime(future_ms)
        assert result is not None
        assert '2099' in result or '2100' in result  # 시스템 timezone에 따라 다를 수 있음
