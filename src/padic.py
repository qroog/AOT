"""
Модуль p-адической организации фактов (p=3).
Путь [a0, a1, a2]:
a0: 0 - системный/документальный, 1 - свидетельство, 2 - правило/интерпретация
a1: 0 - установленный факт, 1 - сообщение/предположение, 2 - спорное/исключение
a2: 0 - до события, 1 - во время события, 2 - после/неизвестно
"""
from typing import List, Tuple, Dict
from src.schemas import Claim

SOURCE_LABELS = {0: "системные/документальные", 1: "свидетельства", 2: "регламенты/правила"}
STATUS_LABELS = {0: "подтверждённые факты", 1: "сообщения/гипотезы", 2: "спорные/исключения"}
TIME_LABELS = {0: "до инцидента", 1: "во время инцидента", 2: "после/неизвестно"}

def compute_padic_code(path: Tuple[int, int, int]) -> int:
    a0, a1, a2 = path
    return a0 + a1 * 3 + a2 * 9

def decode_padic_code(code: int) -> Tuple[int, int, int]:
    a0 = code % 3
    a1 = (code // 3) % 3
    a2 = (code // 9) % 3
    return (a0, a1, a2)

def padic_distance(path_x: Tuple[int, int, int], path_y: Tuple[int, int, int]) -> float:
    """
    d3(x, y) = 3^(-k), где k — длина совпадающего общего префикса (0 <= k <= 3).
    Если совпадают все 3 уровня (k=3), расстояние считается 0.
    """
    k = 0
    for ax, ay in zip(path_x, path_y):
        if ax == ay:
            k += 1
        else:
            break
    if k == 3:
        return 0.0
    return 3.0 ** (-k)

def get_branch_label(path: Tuple[int, int, int]) -> str:
    a0, a1, a2 = path
    return f"{SOURCE_LABELS.get(a0, '')}, {STATUS_LABELS.get(a1, '')}, {TIME_LABELS.get(a2, '')}"

def group_claims_by_padic_branches(
    claims: List[Claim],
    claim_paths: Dict[str, Tuple[int, int, int]]
) -> Dict[Tuple[int, int, int], List[Claim]]:
    branches: Dict[Tuple[int, int, int], List[Claim]] = {}
    for c in claims:
        p = claim_paths.get(c.claim_id, (1, 1, 2))
        branches.setdefault(p, []).append(c)
    # Сортируем ключи по коду/времени для стабильности
    sorted_branches = dict(sorted(branches.items(), key=lambda item: (item[0][0], item[0][1], item[0][2])))
    return sorted_branches

def format_padic_context(
    claims: List[Claim],
    claim_paths: Dict[str, Tuple[int, int, int]]
) -> str:
    branches = group_claims_by_padic_branches(claims, claim_paths)
    lines = []
    for path, b_claims in branches.items():
        desc = get_branch_label(path)
        lines.append(f"ВЕТВЬ [{path[0]},{path[1]},{path[2]}] — {desc}")
        for c in b_claims:
            lines.append(f"{c.claim_id}: {c.text} (Статус: {c.status})")
        lines.append("")
    return "\n".join(lines).strip()
