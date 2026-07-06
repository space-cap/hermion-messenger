import asyncio
import os
from dotenv import load_dotenv

from kiwoom import AsyncKiwoomClient
from kiwoom.models.domestic import Ka10001Request, Ka10066Request, Ka20001Request

# 1. .env 파일의 환경변수 로드
load_dotenv()

APP_KEY = os.getenv("KIWOOM_APP_KEY")
SECRET_KEY = os.getenv("KIWOOM_SECRET_KEY")
IS_MOCK = os.getenv("KIWOOM_IS_MOCK", "true").lower() == "true"

async def test_kiwoom_connection():
    print("=== 키움증권 REST API 연동 테스트 시작 ===")
    
    # API 키 유효성 기본 검사
    if not APP_KEY or not SECRET_KEY or "your_" in APP_KEY:
        print("[경고] .env 파일에 올바른 KIWOOM_APP_KEY 및 KIWOOM_SECRET_KEY를 입력해 주세요.")
        print("현재 설정된 값으로 연동 테스트를 시도하지만, 인증 오류가 발생할 수 있습니다.")
        print(f"설정 상태: APP_KEY={'설정됨' if APP_KEY else '없음'}, IS_MOCK={IS_MOCK}")
        print("=========================================")

    # 2. AsyncKiwoomClient 초기화
    client = AsyncKiwoomClient(
        appkey=APP_KEY or "mock_app_key",
        secretkey=SECRET_KEY or "mock_secret_key",
        is_mock=IS_MOCK
    )

    try:
        # 3. 요청 생성 및 동시(Concurrent) 비동기 호출
        print("\n[1] 데이터 요청 전송 중...")
        
        # A. 삼성전자(005930) 주식 기본 정보 요청
        stk_req = Ka10001Request(stk_cd="005930")
        
        # B. 코스피 종합지수 업종현재가 요청
        kospi_req = Ka20001Request(mrkt_tp="0", inds_cd="001")
        
        # C. 코스닥 종합지수 업종현재가 요청
        kosdaq_req = Ka20001Request(mrkt_tp="1", inds_cd="101")
        
        # D. 코스피 투자자별 당일 순매수 금액 요청
        flow_req = Ka10066Request(
            mrkt_tp="001",      # 코스피
            amt_qty_tp="1",     # 금액
            trde_tp="0",        # 순매수
            stex_tp="1"         # KRX
        )

        # asyncio.gather로 병렬 처리하여 대기 시간 최소화 (Async-First)
        stk_task = client.domestic.ka10001(stk_req)
        kospi_task = client.domestic.ka20001(kospi_req)
        kosdaq_task = client.domestic.ka20001(kosdaq_req)
        flow_task = client.domestic.ka10066(flow_req)
        
        stk_resp, kospi_resp, kosdaq_resp, flow_resp = await asyncio.gather(
            stk_task, kospi_task, kosdaq_task, flow_task,
            return_exceptions=True
        )

        print("\n[2] 데이터 수신 및 결과 확인:")
        
        # A 결과 출력
        if isinstance(stk_resp, Exception):
            print(f"[오류] 삼성전자 시세 조회 실패: {stk_resp}")
        else:
            print(f"[성공] [주식] 종목명: {stk_resp.stk_nm.strip()} | 현재가: {stk_resp.cur_prc}원 | 등락률: {stk_resp.flu_rt}%")

        # B 결과 출력
        if isinstance(kospi_resp, Exception):
            print(f"[오류] 코스피 종합지수 조회 실패: {kospi_resp}")
        else:
            inds_nm = getattr(kospi_resp, "inds_nm", "코스피 종합")
            cur_prc = getattr(kospi_resp, "cur_prc", "N/A")
            flu_rt = getattr(kospi_resp, "flu_rt", "N/A")
            print(f"[성공] [지수] {inds_nm.strip()}: {cur_prc} | 등락률: {flu_rt}%")

        # C 결과 출력
        if isinstance(kosdaq_resp, Exception):
            print(f"[오류] 코스닥 종합지수 조회 실패: {kosdaq_resp}")
        else:
            inds_nm = getattr(kosdaq_resp, "inds_nm", "코스닥 종합")
            cur_prc = getattr(kosdaq_resp, "cur_prc", "N/A")
            flu_rt = getattr(kosdaq_resp, "flu_rt", "N/A")
            print(f"[성공] [지수] {inds_nm.strip()}: {cur_prc} | 등락률: {flu_rt}%")

        # D 결과 출력
        if isinstance(flow_resp, Exception):
            print(f"[오류] 코스피 수급 정보 조회 실패: {flow_resp}")
        else:
            print("[성공] [수급] 코스피 당일 순매수 동향 (상위 필드 확인):")
            for key, val in flow_resp.model_dump().items():
                if val and key in ["frgn_ntby_amt", "inst_ntby_amt", "prvt_ntby_amt"]:
                    print(f"   - {key}: {val} (단위: 억 원 등)")
            print(f"   - 전체 수급 데이터 응답: {flow_resp.model_dump()}")

    except Exception as e:
        print(f"[오류] API 호출 중 예외 발생: {e}")
    finally:
        print("\n=== 테스트 완료 ===")

if __name__ == "__main__":
    asyncio.run(test_kiwoom_connection())
