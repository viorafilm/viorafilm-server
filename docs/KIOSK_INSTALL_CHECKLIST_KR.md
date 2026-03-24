# Viorafilm 키오스크 설치 체크리스트 (배포용 1페이지)

## A. 설치 담당자 체크리스트
### 1) 설치 전 준비
- [ ] 설치 파일 준비: `ViorafilmKiosk_Setup_x.x.x.exe`
- [ ] 장치 정보 준비:
  - `Device Code` (예: `KIOSK101`)
  - `Device Token` (최초 1회 발급 문자열)
- [ ] 인터넷 연결 가능한 Windows PC 확인
- [ ] 카메라/프린터/지폐인식기(사용 매장) 연결 확인

### 2) 설치 실행
- [ ] `ViorafilmKiosk_Setup_x.x.x.exe` 실행
- [ ] 기본 경로로 설치 완료
- [ ] 설치 후 프로그램 실행

### 3) 최초 실행 등록 (필수)
최초 1회 `Device Registration` 창에서 아래 입력:
- `API Base URL`: `https://api.viorafilm.com/api`
- `Device Code`: 관리자 발급 코드
- `Device Token`: 관리자 발급 토큰

실행:
- [ ] `Verify & Save` 클릭

성공 기준:
- [ ] 시작 화면으로 자동 진입
- [ ] 재실행 시 등록 창 미노출

실패 시 조치:
- [ ] 코드/토큰 오타 재확인
- [ ] 인터넷 연결 확인
- [ ] 관리자에 토큰 재발급 요청

## B. 설치 직후 점검 체크리스트 (필수)
- [ ] 시작 화면 정상 진입
- [ ] `F12` 관리자 화면 진입
- [ ] 카메라 라이브뷰 정상
- [ ] 프린터 테스트 출력 정상
- [ ] 결제 테스트 1건 정상
- [ ] QR 페이지 접속 및 다운로드 정상

### TP70(해외 지폐인식기) 매장만
`F12 > Admin Settings`:
- [ ] `Bill Acceptor Profile` = `Overseas (TP70 RS-232 compatible)`
- [ ] `COM Port` 선택 후 지폐 테스트 정상

참고:
- 국가별 지폐 코드/금액 매핑이 다르면 `bill_to_amount` 조정 필요

## C. 운영 시작 완료 기준
- [ ] 서버 대시보드 장치 상태 `ONLINE`
- [ ] 매출관리에서 테스트 결제 확인
- [ ] 쿠폰 사용 시 상태 `USED` 반영 확인
- [ ] QR 링크에서 이미지/비디오 다운로드 확인

## D. 장애 보고 템플릿 (복사해서 전달)
아래 5개를 같이 전달:
- 매장명 / 장치코드
- 앱 버전 (예: `1.0.3`)
- 발생 시간
- 로그 파일 경로: `설치폴더\\logs\\kiosk_YYYYMMDD.log`
- 화면 캡처 1장
