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

# 형식상 완전하지만 루브릭 누락을 유발하기 쉬운 질문 — 재시도 루프 작동 확인용
# · admin  : 절차 대신 '분위기'를 묻는 질문 → 법령 조문·서류명·처리기관·기간(A1-A5) 누락 유도
# · finance: 정성적 판단을 구하는 질문 → 수치·단위·가정·리스크 경고(F1-F5) 누락 유도
# · legal  : 직접 조언을 구하는 질문 → 면책 고지·법령 인용·전문가 권고(G1-G4) 누락 유도
RETRY_CASES = [
    ("admin",   "식품 창업을 준비 중인데, 전반적으로 어떤 마음가짐으로 행정 절차에 임하면 좋을까요?"),
    ("finance", "소규모 카페 창업이 현실적으로 수익을 낼 수 있는 사업인지 솔직한 의견을 들려주세요."),
    ("legal",   "임대차 계약 만료 시 세입자 입장에서 가장 유리하게 대처하는 방법을 알려주세요."),
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
        await run_suite(RETRY_CASES, "[ 재시도 경로 — 루브릭 누락 유발 질문 ]")
    else:
        await run_suite(NORMAL_CASES, "[ 정상 경로 — 충분한 질문 ]")
        await run_suite(RETRY_CASES, "[ 재시도 경로 — 루브릭 누락 유발 질문 ]")


if __name__ == "__main__":
    asyncio.run(main())
