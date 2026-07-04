# KRX Open API 명세서

**버전**: v0.1 (초안 — 승인 후 실제 응답 확인하며 업데이트 필요)
**작성일**: 2026.07.01
**대상**: 주식 모닝브리핑 구독 서비스

---

## 1. 개요

본 문서는 서비스에서 사용할 KRX Open API 6종의 요청/응답 명세를 정리한 문서입니다. 인증키 승인 후, 실제 응답을 받아 각 항목의 필드명·타입·예시값을 채워 완성합니다.

**Base URL (운영)**: `https://data-dbg.krx.co.kr/svc/apis/`
**Base URL (샘플/테스트)**: `https://data-dbg.krx.co.kr/svc/sample/apis/`
> 운영과 샘플이 같은 도메인(`data-dbg.krx.co.kr`) 아래 `apis`와 `sample/apis` 경로로 구분됨. 개발 중에는 sample 경로로 응답 형태를 먼저 확인하고, 실제 서비스 배포 시 운영 경로(`apis`)로 전환.

**인증 방식**: HTTP 요청 헤더에 `AUTH_KEY` 포함
```
GET /svc/apis/idx/kospi_dd_trd?basDd=20260601 HTTP/1.1
Host: data-dbg.krx.co.kr
AUTH_KEY: {발급받은 인증키 — 코드/문서에 하드코딩 금지, 환경변수로 관리}
```
> ⚠️ 보안: AUTH_KEY는 이 문서에 실제 값을 기록하지 않습니다. `.env` 파일 또는 시크릿 매니저에 저장하고, `.gitignore`에 반드시 포함하세요.

---

## 2. 사용 API 목록 (확정 6종)

| 우선순위 | API 명 | API ID | 용도 (PRD 매핑) |
|---|---|---|---|
| High | KOSPI 시리즈 일별시세정보 | `kospi_dd_trd` | FR-1.1 코스피 지수/등락률/거래대금 |
| High | KOSDAQ 시리즈 일별시세정보 | `kosdaq_dd_trd` | FR-1.1 코스닥 지수/등락률/거래대금 |
| High | 유가증권 일별매매정보 | `stk_bydd_trd` | FR-3.3 코스피 개별종목 등락률/거래량 스크리닝 |
| High | 코스닥 일별매매정보 | `ksq_bydd_trd` | FR-3.3 코스닥 개별종목 등락률/거래량 스크리닝 |
| Medium | 유가증권 종목기본정보 | `stk_isu_base_info` | 종목코드 ↔ 종목명 매핑 (코스피) |
| Medium | 코스닥 종목기본정보 | `ksq_isu_base_info` | 종목코드 ↔ 종목명 매핑 (코스닥) — ⚠️ 3.3 확인 결과 매매정보 API에 이미 종목명 포함되어 있어 우선순위 Low로 하향 검토 |

> **엔드포인트 경로 패턴**: 지수 계열은 `/svc/apis/idx/...`, 주식 매매정보 계열은 `/svc/apis/sto/...`로 카테고리별 경로가 다름. 종목기본정보 API도 `/svc/apis/sto/...` 하위일 가능성 높음 (확인 필요).

> 보류: `krx_dd_trd`(KRX 통합지수), ETF/ETN/ELW, 채권, 파생, 일반상품, ESG 계열은 현재 서비스 범위 밖. 향후 확장 시(예: ETF 자금 흐름 섹션) 재검토.
> 미해결: 투자자별(외국인/기관/개인) 매매동향은 이 카탈로그에 없음 → KIS Open API 대체 여부 확인 필요 (별도 문서 "수급데이터 소스 검토" 참고)

---

## 3. API별 상세 명세

### 3.1 KOSPI 시리즈 일별시세정보 (`kospi_dd_trd`) ✅ 확인 완료

| 항목 | 내용 |
|---|---|
| 설명 | KOSPI 시리즈 지수의 일별 시세정보 |
| 데이터 제공 시작일 | 2010-01-04 |
| Endpoint | `GET /svc/apis/idx/kospi_dd_trd` |
| 요청 방식 | GET |
| 요청 파라미터 | `basDd` (string, 기준일자 YYYYMMDD) |

**요청 예시**
```
GET /svc/apis/idx/kospi_dd_trd?basDd=20260601 HTTP/1.1
Host: data-dbg.krx.co.kr
AUTH_KEY: {인증키}
```

**응답 필드 (OutBlock_1, 배열 — 여러 KOSPI 계열 지수가 함께 반환됨)**

| 필드명 | 타입 | 설명 |
|---|---|---|
| `BAS_DD` | string | 기준일자 |
| `IDX_CLSS` | string | 계열구분 |
| `IDX_NM` | string | 지수명 (예: "코스피", "코스피 200" 등 여러 개 포함될 것으로 추정) |
| `CLSPRC_IDX` | string | 종가 |
| `CMPPREVDD_IDX` | string | 대비 |
| `FLUC_RT` | string | 등락률 |
| `OPNPRC_IDX` | string | 시가 |
| `HGPRC_IDX` | string | 고가 |
| `LWPRC_IDX` | string | 저가 |
| `ACC_TRDVOL` | string | 거래량 |
| `ACC_TRDVAL` | string | 거래대금 |
| `MKTCAP` | string | 상장시가총액 |

> ⚠️ 모든 필드가 **string 타입**으로 반환됨 — 숫자 비교/포맷팅 전 반드시 파싱(콤마 제거 후 float/int 변환) 필요. 검증 레이어(FR-4) 구현 시 이 점 반영.
> ⚠️ 응답이 배열(`OutBlock_1: [...]`)이므로, 여러 지수 중 `IDX_NM`이 "코스피"(정확한 명칭은 실응답 확인 필요)인 항목만 필터링하는 로직 필요.
> ✅ **[실제 응답 확인]** 실호출 결과 `IDX_NM`에는 "코스피 100", "코스피200제외 코스피지수", "코스피 200 건설", "코스피 200 철강/소재", "종이·목재", "비금속", "금융", "증권" 등 **세부 업종/파생 지수들이 대량으로 포함**되어 있음. 정작 브리핑에 필요한 **"코스피" 그 자체(종합주가지수)**는 이번 샘플 10개 안에는 없었음 — 전체 배열이 더 크고 뒤쪽 어딘가에 있을 가능성이 높음. **전체 응답을 받아서 `IDX_NM == "코스피"`(정확한 문자열은 재확인 필요, 후보: "코스피", "코스피종합지수" 등)로 필터링하는 로직 필요**.
> ⚠️ **데이터 값 관련 주의**: 이번 샘플의 수치(코스피100 등락률 +6.72%, 대비 +642.85 등)가 일반적인 하루 변동폭치고 비정상적으로 큼. `data-dbg.krx.co.kr` 도메인이 테스트/디버그 서버인 점을 감안하면 **실제 시장 데이터가 아닌 테스트용 더미 데이터일 가능성**이 있음. 운영 배포 전 실제 운영 도메인(정식 API 키 발급 후 안내받는 프로덕션 엔드포인트)에서도 동일하게 동작하는지, 그리고 그 값이 실제 시장과 일치하는지 반드시 재검증 필요.

**서비스 매핑**: `MarketDataSnapshot.domestic_index.kospi` ← `CLSPRC_IDX`, `FLUC_RT`, `ACC_TRDVAL`

### 3.2 KOSDAQ 시리즈 일별시세정보 (`kosdaq_dd_trd`) ✅ 확인 완료

| 항목 | 내용 |
|---|---|
| 설명 | KOSDAQ 시리즈 지수의 일별 시세정보 |
| 데이터 제공 시작일 | 2010-01-04 |
| Endpoint | `GET /svc/apis/idx/kosdaq_dd_trd` |
| 요청 방식 | GET |
| 요청 파라미터 | `basDd` (string, 기준일자 YYYYMMDD) |

**응답 필드 (OutBlock_1)**: 3.1 KOSPI와 완전히 동일한 구조 (`BAS_DD`, `IDX_CLSS`, `IDX_NM`, `CLSPRC_IDX`, `CMPPREVDD_IDX`, `FLUC_RT`, `OPNPRC_IDX`, `HGPRC_IDX`, `LWPRC_IDX`, `ACC_TRDVOL`, `ACC_TRDVAL`, `MKTCAP`)

> 모든 값 string 타입, 배열 응답(여러 KOSDAQ 계열 지수 포함) — KOSPI와 동일한 파싱/필터링 로직 재사용 가능. 공통 파서 함수 하나로 KOSPI/KOSDAQ 둘 다 처리 가능할 것으로 보임.

**서비스 매핑**: `MarketDataSnapshot.domestic_index.kosdaq` ← `CLSPRC_IDX`, `FLUC_RT`, `ACC_TRDVAL`

### 3.3 유가증권 일별매매정보 (`stk_bydd_trd`) ✅ 확인 완료

| 항목 | 내용 |
|---|---|
| 설명 | 유가증권시장 상장 주권의 일별 매매정보 (전 종목) |
| 데이터 제공 시작일 | 2010-01-04 |
| Endpoint | `GET /svc/apis/sto/stk_bydd_trd` |
| 요청 방식 | GET |
| 요청 파라미터 | `basDd` (string, 기준일자 YYYYMMDD) — **종목코드 파라미터 없음 → 전 종목이 한 번에 배열로 반환됨 (확인됨)** |

**응답 필드 (OutBlock_1, 배열 — 전 종목)**

| 필드명 | 타입 | 설명 |
|---|---|---|
| `BAS_DD` | string | 기준일자 |
| `ISU_CD` | string | 종목코드 |
| `ISU_NM` | string | 종목명 |
| `MKT_NM` | string | 시장구분 |
| `SECT_TP_NM` | string | 소속부 |
| `TDD_CLSPRC` | string | 종가 |
| `CMPPREVDD_PRC` | string | 대비 |
| `FLUC_RT` | string | 등락률 |
| `TDD_OPNPRC` | string | 시가 |
| `TDD_HGPRC` | string | 고가 |
| `TDD_LWPRC` | string | 저가 |
| `ACC_TRDVOL` | string | 거래량 |
| `ACC_TRDVAL` | string | 거래대금 |
| `MKTCAP` | string | 시가총액 |
| `LIST_SHRS` | string | 상장주식수 |

> ✅ **중요**: `ISU_CD`(종목코드)와 `ISU_NM`(종목명)이 이 응답에 이미 포함되어 있음 → **별도의 종목기본정보 API(`stk_isu_base_info`) 호출 없이도 종목코드-이름 매핑이 가능**. top_movers 스크리닝(FR-3.3)에 필요한 데이터가 이 API 하나로 충분히 해결됨. 종목기본정보 API는 상장일 등 부가정보가 꼭 필요한 경우에만 우선순위를 Low로 낮춰도 될 것으로 판단됨.
> ✅ **[해결됨] 코드 체계 확인 완료**: 실제 응답 샘플 확인 결과, `ISU_CD`는 `"415640"`, `"330590"`, `"088980"` 등 **6자리 형태**로 반환됨. 종목기본정보 API의 `ISU_SRT_CD`(단축코드)와 동일한 체계로 판단됨(12자리 표준코드/ISIN 아님). 두 API를 조인할 경우 `stk_bydd_trd.ISU_CD` ↔ `stk_isu_base_info.ISU_SRT_CD`로 매핑.
> ⚠️ **샘플 데이터 주의**: 확인해주신 응답 샘플이 전부 리츠(REITs)/인프라펀드(KB발해인프라, 롯데리츠, 맥쿼리인프라 등)로만 구성되어 있음. 실제 코스피 전 종목(삼성전자 등 일반 종목 포함)이 맞는지, 또는 `sample` 엔드포인트의 고정 더미 데이터 일부만 보여주는 건지 확인 필요. 운영 엔드포인트로 실호출 시 전체 시장 종목이 다 나오는지 재확인 권장.
> ⚠️ **[업데이트]** `kospi_dd_trd` 실호출 결과에서도 등락률이 비정상적으로 큰 값(+6.72% 등)이 확인되어, `data-dbg.krx.co.kr` 자체가 **테스트/디버그용 더미 데이터를 반환하는 서버일 가능성**이 제기됨. 이 서버로는 구조(필드명, 배열 형태) 파악용으로 활용하고, 실제 프로덕션 배포 전에는 정식 운영 엔드포인트(발급 승인 문서에서 별도 안내받을 것으로 예상)로 재검증 필요.
> ⚠️ 전 종목이 배열로 오므로, 서버 측에서 `FLUC_RT`(등락률) 또는 `ACC_TRDVAL`(거래대금) 기준 내림차순 정렬 후 상위 N개를 추출하는 로직 구현 필요 (top_movers).
> ⚠️ 모든 값 string 타입 — 콤마 제거 후 형변환 필요.

**서비스 매핑**: `top_movers` 스크리닝 (FR-3.3)의 기초 데이터

### 3.4 코스닥 일별매매정보 (`ksq_bydd_trd`) ✅ 확인 완료

| 항목 | 내용 |
|---|---|
| 설명 | 코스닥시장 상장 주권의 일별 매매정보 (전 종목) |
| 데이터 제공 시작일 | 2010-01-04 |
| Endpoint | `GET /svc/apis/sto/ksq_bydd_trd` |
| 요청 방식 | GET |
| 요청 파라미터 | `basDd` (string, 기준일자 YYYYMMDD) |

**응답 필드**: 3.3 유가증권 일별매매정보와 완전히 동일한 구조 (`ISU_CD`, `ISU_NM`, `MKT_NM`, `SECT_TP_NM`, `TDD_CLSPRC`, `CMPPREVDD_PRC`, `FLUC_RT`, `TDD_OPNPRC`, `TDD_HGPRC`, `TDD_LWPRC`, `ACC_TRDVOL`, `ACC_TRDVAL`, `MKTCAP`, `LIST_SHRS`)

> 3.3과 동일한 파서/스크리닝 로직 재사용 가능. 코드 구현 시 `market` 파라미터(kospi/kosdaq)만 다르게 받는 공통 함수로 설계하면 중복 최소화 가능.

**서비스 매핑**: 코스닥 `top_movers` 스크리닝 (FR-3.3)

### 3.5 유가증권 종목기본정보 (`stk_isu_base_info`) ✅ 확인 완료

| 항목 | 내용 |
|---|---|
| 설명 | 유가증권시장 종목의 기본 정보 |
| 데이터 제공 시작일 | 2010-01-04 |
| Endpoint | `GET /svc/apis/sto/stk_isu_base_info` |
| 요청 방식 | GET |
| 요청 파라미터 | `basDd` (string, 기준일자 YYYYMMDD) |

**응답 필드 (OutBlock_1, 배열 — 전 종목)**

| 필드명 | 타입 | 설명 |
|---|---|---|
| `ISU_CD` | string | **표준코드** (12자리 ISIN 형태로 추정) |
| `ISU_SRT_CD` | string | **단축코드** (일반적으로 쓰는 6자리 종목코드로 추정, 예: "005930") |
| `ISU_NM` | string | 한글 종목명 |
| `ISU_ABBRV` | string | 한글 종목약명 |
| `ISU_ENG_NM` | string | 영문 종목명 |
| `LIST_DD` | string | 상장일 |
| `MKT_TP_NM` | string | 시장구분 |
| `SECUGRP_NM` | string | 증권구분 |
| `SECT_TP_NM` | string | 소속부 |
| `KIND_STKCERT_TP_NM` | string | 주식종류 |
| `PARVAL` | string | 액면가 |
| `LIST_SHRS` | string | 상장주식수 |

> ⚠️ **중요 — 코드 체계 불일치 가능성**: 이 API의 `ISU_CD`는 "표준코드"(12자리 ISIN 추정)인데, 3.3/3.4 매매정보 API의 `ISU_CD`는 그냥 "종목코드"로만 표기되어 있어 **두 API의 `ISU_CD`가 같은 값 체계인지 다른지 확인 필요**. 만약 매매정보 API의 `ISU_CD`가 실제로는 "단축코드"(6자리) 체계라면, 두 API를 조인(join)할 때 `ISU_CD` 대 `ISU_SRT_CD`로 매핑해야 함. **실제 응답값을 나란히 비교해서 확인 필수** (예: 삼성전자 조회 시 두 API에서 나오는 코드 값 비교).
> 참고: 3.3/3.4에서 이미 `ISU_NM`(종목명)이 함께 제공되므로, 이름 매핑 목적이라면 이 API 없이도 충분함 (이전 메모 참고). 이 API는 상장일(`LIST_DD`), 액면가, 상장주식수 등 **부가 정적 정보가 필요할 때만** 사용.

**서비스 매핑**: 종목코드 정합성 검증 및 부가 정보 조회용 (Low 우선순위, 필요 시 사용)

### 3.6 코스닥 종목기본정보 (`ksq_isu_base_info`) ✅ 확인 완료

| 항목 | 내용 |
|---|---|
| 설명 | 코스닥시장 종목의 기본 정보 |
| Endpoint | `GET /svc/apis/sto/ksq_isu_base_info` |
| 요청 방식 | GET |
| 요청 파라미터 | `basDd` (string, 기준일자 YYYYMMDD) |

**응답 필드**: 3.5 유가증권 종목기본정보와 완전히 동일한 구조 (`ISU_CD` 표준코드, `ISU_SRT_CD` 단축코드, `ISU_NM`, `ISU_ABBRV`, `ISU_ENG_NM`, `LIST_DD`, `MKT_TP_NM`, `SECUGRP_NM`, `SECT_TP_NM`, `KIND_STKCERT_TP_NM`, `PARVAL`, `LIST_SHRS`)

**서비스 매핑**: 3.5와 동일 — 코드 체계 정합성 확인 및 부가 정보 조회용 (Low 우선순위)

---

## 4. 공통 처리 규칙

| 규칙 | 설명 |
|---|---|
| 호출 시각 | 매일 07:00 KST (전일 확정 데이터 기준) |
| 재시도 | 실패 시 최대 3회, 각 재시도 간 30초 간격 (PRD FR-1.5) |
| 타임아웃 | 요청당 10초 (임시값, 실측 후 조정) |
| 데이터 캐싱 | 종목기본정보(3.5, 3.6)는 매일 갱신할 필요 없이 주 1회 갱신으로 캐싱 |
| Rate Limit | (승인 문서에서 확인 필요 — 초당/일일 호출 제한 존재 여부) |

---

## 5. 미해결 항목 (승인 후 채워야 할 것)

- [x] 인증키 전달 방식 → 헤더 `AUTH_KEY` (확인 완료, 3.1 기준)
- [x] 유가증권 일별매매정보(`stk_bydd_trd`) 확인 완료 → 전 종목 배열 반환, 종목명 포함됨
- [x] 코스닥 일별매매정보(`ksq_bydd_trd`) 확인 완료 → 유가증권과 동일 구조
- [x] 유가증권 종목기본정보(`stk_isu_base_info`) 확인 완료 → 표준코드/단축코드 구분 발견
- [x] 코스닥 종목기본정보(`ksq_isu_base_info`) 확인 완료 → 유가증권과 동일 구조
- [x] **[해결됨]** 매매정보 API의 `ISU_CD`는 6자리(단축코드) 체계로 확인됨
- [ ] 응답 샘플이 리츠/인프라펀드 위주로만 나온 것이 전체 시장 데이터인지, sample 엔드포인트의 제한된 더미 데이터인지 확인 필요 — 삼성전자 등 대형주가 포함되는지 재확인
- [ ] **[중요, 미해결]** `kospi_dd_trd` 실호출 결과 "코스피" 그 자체(종합주가지수)가 10개 샘플 안에 없었음 — 전체 배열을 받아 정확한 `IDX_NM` 문자열 확인 필요 (업종별 세부지수가 수십~백여 개 섞여 있을 것으로 추정)
- [ ] **[중요, 신규]** `data-dbg.krx.co.kr`가 실제 시장 데이터가 아닌 테스트용 더미 데이터를 반환하는 서버일 가능성 있음 (등락률 +6.72% 등 비정상적 수치 확인됨) — 운영 배포 전 정식 프로덕션 엔드포인트 확인 및 실데이터 검증 필수
- [ ] Rate Limit / 호출 제한 정책 (승인 문서 또는 콘솔에서 확인)
- [ ] 응답 데이터 인코딩 (EUC-KR 여부 등)
- [ ] 투자자별 매매동향(수급) 데이터 대체 소스 확정 (KIS API 확인 필요) — 이 카탈로그에 없는 것 재확인됨

**진행 상태**: KRX Open API 확정 6종 구조 파악 완료 ✅, 종목코드 체계 정합성 확인 완료 ✅. 단, **dbg 서버가 더미 데이터일 가능성**이 있어 운영 전 정식 엔드포인트 재검증이 반드시 필요한 상태로 전환됨.

---

## 6. 참고 문서

- PRD: `PRD_요구사항정의서.md`
- 사업기획서: `주식모닝브리핑_구독서비스_기획서.md`
