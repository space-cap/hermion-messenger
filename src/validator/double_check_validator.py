import re
from typing import Dict, Any, Set, List, Optional

class DoubleCheckValidator:
    """LLM이 생성한 브리핑 본문 내 숫자가 원본 금융 데이터셋과 일치하는지 검증하는 검증 엔진"""
    
    # 무시할 공통 수치 (연도, 마크다운 순서 번호, 일반 백분율 등 오탐 방지용)
    IGNORE_NUMBERS = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 2026, 100}
    
    @staticmethod
    def extract_numbers_from_text(text: str) -> List[str]:
        """텍스트 본문에서 숫자 포맷(부호, 콤마, 소수점, 백분율 포함)의 문자열들을 추출합니다."""
        # 콤마, 부호, 소수점, %가 포함된 숫자 추출 정규식
        pattern = r"[-+]?[0-9,]+(?:\.[0-9]+)?%?"
        return re.findall(pattern, text)
        
    @staticmethod
    def normalize_number(num_str: str) -> Optional[float]:
        """숫자 형태의 문자열을 콤마와 퍼센트 기호를 제거하고 float 값으로 정규화합니다."""
        clean_str = num_str.replace(",", "").replace("%", "")
        # 앞뒤의 부호(+, -)는 유연한 대조를 위해 제거하거나 파싱 가능하도록 함
        # 여기서는 float 변환 후 절대값 대조 등을 위해 일단 float 변환을 시도
        try:
            return float(clean_str)
        except ValueError:
            return None

    def collect_all_numbers_from_source(self, data: Any) -> Set[float]:
        """원본 데이터셋(dict, list 등)을 재귀적으로 순회하여 모든 수치형 값을 수집합니다."""
        numbers = set()
        
        if isinstance(data, dict):
            for key, val in data.items():
                # 딕셔너리의 키가 종목코드 등 숫자 형식일 경우 추출 대상에 반영
                try:
                    clean_key = str(key).replace(",", "").replace("%", "")
                    numbers.add(float(clean_key))
                except ValueError:
                    pass
                numbers.update(self.collect_all_numbers_from_source(val))
        elif isinstance(data, list):
            for item in data:
                numbers.update(self.collect_all_numbers_from_source(item))
        elif isinstance(data, (int, float)):
            # 수치형인 경우 추가
            numbers.add(float(data))
        elif isinstance(data, str):
            # 문자열인 경우 부호나 콤마 등을 떼고 float로 변환 가능한지 시도
            # 예: "+2.75", "-8,051.33" 등
            clean = data.replace(",", "").replace("%", "")
            try:
                numbers.add(float(clean))
            except ValueError:
                # 일반 텍스트 내에 섞여 있는 숫자 추출 시도
                extracted = self.extract_numbers_from_text(data)
                for num_str in extracted:
                    normalized = self.normalize_number(num_str)
                    if normalized is not None:
                        numbers.add(normalized)
                        
        return numbers

    def validate_briefing(self, briefing_text: str, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        생성된 브리핑 텍스트 내 모든 수치가 원본 데이터셋에 존재하는지 검증합니다.
        
        :param briefing_text: Claude가 생성한 마크다운 브리핑 텍스트
        :param raw_data: API로 수집한 원래의 금융 정보 딕셔너리
        :return: {'is_valid', 'mismatched_numbers', 'valid_percentage'}
        """
        # 1. 원본 데이터셋 내 모든 숫자 추출 및 수집
        source_numbers = self.collect_all_numbers_from_source(raw_data)
        
        # 2. 브리핑 텍스트 내 모든 숫자 추출
        extracted_briefing_strs = self.extract_numbers_from_text(briefing_text)
        
        mismatched = []
        checked_count = 0
        
        # 3. 각 숫자 대조
        for num_str in extracted_briefing_strs:
            normalized = self.normalize_number(num_str)
            if normalized is None:
                continue
                
            # 무시할 공통 수치는 패스
            if int(normalized) in self.IGNORE_NUMBERS if normalized.is_integer() else False:
                continue
                
            checked_count += 1
            
            # 절대값 매치 및 일반 매치 검증
            # LLM이 등락률 부호(예: -0.45)를 절대값(0.45)으로 변환해서 쓰거나,
            # 반대로 쓰는 경우도 포괄하기 위해 양수/음수/절대값을 다각도로 체크
            matched = False
            for src_num in source_numbers:
                # 부동소수점 오차(예: 2580.12 대 2580.1200000000003)를 고려해 근접도 비교 (오차 허용치 0.001)
                if abs(abs(normalized) - abs(src_num)) < 0.001:
                    matched = True
                    break
                    
            if not matched:
                mismatched.append(num_str)
                
        is_valid = len(mismatched) == 0
        valid_pct = 100.0
        if checked_count > 0:
            valid_pct = round(((checked_count - len(mismatched)) / checked_count) * 100, 2)
            
        return {
            "is_valid": is_valid,
            "mismatched_numbers": list(set(mismatched)),  # 중복 제거된 미스매치 리스트
            "checked_count": checked_count,
            "valid_percentage": valid_pct
        }
