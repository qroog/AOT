"""Модуль p-адической иерархии фактов (p=3, путь [a0, a1, a2])."""
from typing import List, Tuple, Dict
from src.schemas import Claim

SRC_L = {0: "системные/документальные", 1: "свидетельства", 2: "регламенты/правила"}
STS_L = {0: "подтверждённые", 1: "сообщения/гипотезы", 2: "спорные/исключения"}
TIM_L = {0: "до события", 1: "во время", 2: "после/неизвестно"}

def compute_padic_code(p: Tuple[int, int, int]) -> int:
    return p[0] + p[1] * 3 + p[2] * 9

def decode_padic_code(c: int) -> Tuple[int, int, int]:
    return (c % 3, (c // 3) % 3, (c // 9) % 3)

def padic_distance(px: Tuple[int, int, int], py: Tuple[int, int, int]) -> float:
    k = next((i for i, (x, y) in enumerate(zip(px, py)) if x != y), 3)
    return 0.0 if k == 3 else 3.0 ** (-k)

def get_branch_label(p: Tuple[int, int, int]) -> str:
    return f"{SRC_L.get(p[0],'')}, {STS_L.get(p[1],'')}, {TIM_L.get(p[2],'')}"

def group_claims_by_padic_branches(claims: List[Claim], paths: Dict[str, Tuple[int, int, int]]) -> Dict[Tuple[int, int, int], List[Claim]]:
    res: Dict[Tuple[int, int, int], List[Claim]] = {}
    for c in claims:
        res.setdefault(paths.get(c.claim_id, (1, 1, 2)), []).append(c)
    return dict(sorted(res.items()))

def format_padic_context(claims: List[Claim], paths: Dict[str, Tuple[int, int, int]]) -> str:
    out = []
    for p, b_claims in group_claims_by_padic_branches(claims, paths).items():
        out.append(f"ВЕТВЬ [{p[0]},{p[1]},{p[2]}] — {get_branch_label(p)}")
        out.extend(f"{c.claim_id}: {c.text} (Статус: {c.status})" for c in b_claims)
        out.append("")
    return "\n".join(out).strip()
