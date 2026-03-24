# GoDaddy Smart Terminal Payment Integration

## 구조
- 키오스크 UI는 기존 `app/main.py` 화면 흐름을 유지하고, 결제는 `payments/` provider abstraction 뒤로 분리했다.
- `payments/mock_provider.py` 는 오늘 바로 테스트 가능한 MOCK 결제를 제공한다.
- `payments/godaddy_posbridge_provider.py` 는 공식 `PoyntPOSBridge.dll` 을 PowerShell bridge로 호출한다.
- 공식 SDK 원본은 `vendor/poynt-pos-connector-windows-sdk/` 아래에 확보했고, MSI는 `vendor/poynt-pos-connector-windows-sdk/PoyntPOSBridgeSampleInstaller-1.0.180.msi` 이다.
- 추출된 SDK 경로는 `vendor/poynt-pos-connector-windows-sdk/extracted/PoyntPOSBridgeSample/` 이며, 여기의 `PoyntPOSBridge.dll` 을 기본 사용한다.
- 거래 저장은 SQLite `out/payments.sqlite3` 로 분리되며, 카드 민감정보는 저장하지 않는다.

## Mock 모드 사용법
1. 관리자 화면에서 `pay_card` 를 활성화한다.
2. 카드 결제 설정에서 `payment_enabled=ON`, `provider=mock` 로 둔다.
3. 시뮬레이션 결과를 `approve / decline / cancel / timeout` 중 하나로 고른다.
4. `simulation_delay_sec` 로 지연 시간을 조정한다.
5. 결제 화면 진입 후 기존 흐름대로 MOCK 승인/실패를 끝까지 테스트한다.

## Live 모드 전환 방법
1. 관리자 화면에서 provider 를 `godaddy_posbridge` 로 바꾼다.
2. 아래 값을 입력한다.
   - `terminal_ip`
   - `terminal_port`
   - `terminal_name`
   - `pairing_code_or_key`
3. 실단말기 브리지/SDK가 저장소에 없으면 provider 는 실패 메시지를 보여주고 앱은 계속 동작한다.
4. 기본 우선순위는 아래와 같다.
   - `vendor/poynt-pos-connector-windows-sdk/extracted/PoyntPOSBridgeSample`
   - `C:\Program Files (x86)\PoyntPOSBridgeSample`
5. 필요하면 `payment_config.json` 의 `extra.sdk_dir` 로 SDK 경로를 강제할 수 있다.

## 내일 단말기 확인 시 필요한 값
- `terminal_ip`
- `terminal_port`
- `pairing code/key`
- 관리자 화면의 `provider` 전환 위치

## 장애 점검 순서
1. 관리자 진단 패널에서 현재 provider / IP / 포트를 확인한다.
2. `Pair Test` 를 실행한다.
3. `Ping Test` 를 실행한다.
4. 실패하면 `payments.log` 와 최근 거래 목록을 확인한다.
5. 실단말기 브리지 미구성 상태면 `mock` 으로 전환해 전체 플로우가 정상인지 먼저 검증한다.

## 로그 파일 위치
- 일반 앱 로그: `logs/kiosk_YYYYMMDD.log`
- 결제 로그: `logs/payments.log`
- 거래 DB: `out/payments.sqlite3`
