# -*- coding: utf-8 -*-
"""BTC 가격 급변동 알림 — 자동매매 봇(bot.py)과 완전히 무관한 독립 스크립트.

GitHub Actions에서 주기 실행되며, 빗썸 공개 API(인증 불필요)만 사용한다.
API 키·시크릿 등 거래 계정 정보는 이 스크립트 어디에도 없음 — 봇과 코드/자격증명이
완전히 분리되어 있어, 이 저장소가 노출되거나 잘못돼도 매매 계정엔 영향이 없다.

동작: WINDOW_MIN 분 창 안에서 THRESHOLD_PCT% 이상 움직이면 텔레그램 알림.
      알림 후 기준가를 현재가로 리셋(스팸 방지). 창을 그냥 넘기면 기준가를 굴려서 갱신
      (누적 드리프트가 아니라 "짧은 구간 내 급변동"만 감지).

기본값 근거 (즉시 포착이 필요 없다는 전제로 최적화):
  WINDOW_MIN=60   1시간 기준 정상 변동폭은 대략 ±0.6%대(일 변동성 3% 가정, √t 스케일링)
  THRESHOLD_PCT=2.5  정상 변동의 약 4배 — 노이즈가 아닌 "의미있는 급변동"만 통과
  체크 주기는 워크플로(cron)에서 15분으로 설정 — 창(60분) 안에서 4회 샘플링, 해상도 충분

재배포 없이 조정하려면 워크플로 파일의 env: WINDOW_MIN / THRESHOLD_PCT 값만 바꾸면 됨.
"""
import json
import os
from datetime import datetime
from pathlib import Path

import requests

STATE_FILE = Path(__file__).parent / "state.json"

WINDOW_MIN = float(os.environ.get("WINDOW_MIN", 60))
THRESHOLD_PCT = float(os.environ.get("THRESHOLD_PCT", 2.5))


def current_price():
    """빗썸 공개 API 현재가 (인증 불필요, bot.py와 동일 소스)."""
    r = requests.get("https://api.bithumb.com/v1/ticker?markets=KRW-BTC", timeout=10)
    r.raise_for_status()
    return float(r.json()[0]["trade_price"])


def notify(msg):
    tok, chat = os.environ.get("TELEGRAM_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not tok or not chat:
        print("(TELEGRAM_TOKEN/TELEGRAM_CHAT_ID 미설정 — 콘솔에만 출력)")
        print(msg)
        return
    try:
        requests.post(f"https://api.telegram.org/bot{tok}/sendMessage",
                      json={"chat_id": chat, "text": msg}, timeout=10)
    except Exception as e:
        print(f"텔레그램 전송 실패: {e}")


def main():
    now = datetime.utcnow()
    price = current_price()

    if STATE_FILE.exists():
        st = json.loads(STATE_FILE.read_text())
        ref_price = st["ref_price"]
        ref_time = datetime.fromisoformat(st["ref_time"])
    else:
        ref_price, ref_time = price, now

    elapsed_min = (now - ref_time).total_seconds() / 60
    change = (price / ref_price - 1) * 100

    if abs(change) >= THRESHOLD_PCT:
        direction = "🚀 급등" if change > 0 else "💥 급락"
        notify(f"{direction} 감지 (매매 봇과 무관한 가격 알림)\n"
               f"{elapsed_min:.0f}분 새 {change:+.2f}%\n"
               f"{ref_price:,.0f}원 → {price:,.0f}원")
        ref_price, ref_time = price, now
    elif elapsed_min >= WINDOW_MIN:
        ref_price, ref_time = price, now

    STATE_FILE.write_text(json.dumps({"ref_price": ref_price, "ref_time": ref_time.isoformat()}))
    print(f"[{now.isoformat()}] price={price:,.0f} change={change:+.2f}% (ref {elapsed_min:.0f}min ago)")


if __name__ == "__main__":
    main()
