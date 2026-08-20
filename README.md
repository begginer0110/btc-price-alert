# BTC 가격 급변동 알림 (독립 저장소)

`bot.py` 자동매매와는 완전히 분리된 알림 전용 프로젝트입니다. 빗썸 공개 API만 사용하고
거래 계정 API 키가 전혀 없어서, 이 저장소가 어디에 올라가도(퍼블릭이어도) 매매 계정은
전혀 노출되지 않습니다.

## 설정 순서

1. **새 GitHub 저장소 생성** (예: `btc-price-alert`). Public으로 만들어도 안전합니다
   (민감정보 없음). Private을 원하면 그래도 됩니다.

2. **이 폴더를 그대로 push**합니다. 맥 터미널에서:
   ```bash
   cd 이 폴더 경로
   git init
   git add .
   git commit -m "init"
   git branch -M main
   git remote add origin https://github.com/사용자명/btc-price-alert.git
   git push -u origin main
   ```

3. **텔레그램 시크릿 등록**: 저장소 → Settings → Secrets and variables → Actions →
   New repository secret 에서 두 개 추가
   - `TELEGRAM_TOKEN` — 자동매매 프로젝트의 `config.json`에 있는 값과 동일하게 입력
   - `TELEGRAM_CHAT_ID` — 위와 동일

4. **워크플로 쓰기 권한 켜기**: 저장소 → Settings → Actions → General →
   Workflow permissions → **Read and write permissions** 선택 후 저장.
   (state.json을 커밋하려면 필요)

5. **테스트**: 저장소 → Actions 탭 → "BTC 가격 급변동 알림" → Run workflow 로 수동 1회 실행.
   로그에 `price=... change=...` 한 줄이 찍히면 정상. 이후 15분마다 자동 실행됩니다.

## 파라미터 조정

`.github/workflows/price_alert.yml` 안의 `WINDOW_MIN`, `THRESHOLD_PCT` 값만 바꿔서
커밋하면 재배포 없이 즉시 반영됩니다. 기본값: 60분 창 / 2.5% 임계값.

## 동작 원리

- 15분마다 실행, 직전 실행에서 저장한 기준가(`state.json`, git에 커밋되어 다음 실행이 이어받음)와 비교
- 60분 안에 ±2.5% 이상 움직이면 텔레그램 알림 후 기준가 리셋(스팸 방지)
- 60분이 그냥 지나면 기준가를 현재가로 굴려서 갱신 (누적 드리프트 아닌 "구간 내 급변동"만 감지)
