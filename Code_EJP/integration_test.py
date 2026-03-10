"""
연동 테스트: 오케스트레이터 → 하위 에이전트 → Sign-off Agent 전체 루프 검증

실행:
    python integration_test.py           # 전체 시나리오
    python integration_test.py normal    # 정상 경로만
    python integration_test.py retry     # 재시도 경로만
"""

import asyncio
import json
import sys

from orchestrator import run

# ── 시나리오 정의 ─────────────────────────────────────────────
NORMAL_CASES = [
    ("admin",   "식품 가게를 창업하려고 하는데 영업신고는 어떻게 하나요?"),
    ("finance", "소규모 카페 창업 시 초기 6개월 재무 시뮬레이션을 보여주세요. 초기 투자금은 5,000만 원입니다."),
    ("legal",   "임대차 계약 만료 후 집주인이 보증금을 돌려주지 않으면 어떻게 하나요?"),
]

# 의도적으로 불완전한 질문 — 재시도 루프 작동 확인용
RETRY_CASES = [
    ("admin",   "신고요?"),
    ("finance", "돈"),
    ("legal",   "법이요?"),
]


def print_result(result: dict) -> None:
    status = result["status"]
    symbol = "APPROVED" if status == "approved" else "ESCALATED"
    print(f"  상태     : {symbol}")
    print(f"  재시도   : {result['retry_count']}회")
    print(f"  request_id: {result['request_id']}")

    if status == "escalated":
        print(f"  메시지   : {result.get('message', '')}")

    if result["rejection_history"]:
        print(f"  거부 이력 ({len(result['rejection_history'])}건):")
        for h in result["rejection_history"]:
            issues = [i["code"] for i in h["verdict"].get("issues", [])]
            print(f"    시도 {h['attempt']}: issues={issues}")

    print(f"\n  최종 draft:\n{result['draft']}")


async def run_suite(cases: list, label: str) -> None:
    print(f"\n{'#' * 64}")
    print(f"  {label}")
    print(f"{'#' * 64}")

    passed = 0
    failed = 0

    for domain, question in cases:
        print(f"\n{'=' * 52}")
        print(f"  도메인  : {domain.upper()}")
        print(f"  질문    : {question}")
        print("=" * 52)

        result = await run(domain, question, max_retries=3)
        print_result(result)

        if result["status"] == "approved":
            passed += 1
        else:
            failed += 1

    print(f"\n{'─' * 52}")
    print(f"  결과: {passed}건 승인 / {failed}건 에스컬레이션")


async def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"

    if mode == "normal":
        await run_suite(NORMAL_CASES, "[ 정상 경로 — 충분한 질문 ]")
    elif mode == "retry":
        await run_suite(RETRY_CASES, "[ 재시도 경로 — 불완전한 질문 ]")
    else:
        await run_suite(NORMAL_CASES, "[ 정상 경로 — 충분한 질문 ]")
        await run_suite(RETRY_CASES, "[ 재시도 경로 — 불완전한 질문 ]")


if __name__ == "__main__":
    asyncio.run(main())
