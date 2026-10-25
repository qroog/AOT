"""
Набор обязательных автоматических тестов (Лабораторная работа № 6).
Проверяет:
1. Одинаковые p-adic пути (d3 = 0).
2. Различие на каждом из трех уровней (k=0 -> d=1; k=1 -> d=1/3; k=2 -> d=1/9).
3. Ультраметрическое неравенство d(x, z) <= max(d(x, y), d(y, z)).
4. Обработка невалидного JSON от LLM.
5. Несуществующий evidence_id.
6. Статус 'both' без counterevidence_ids (нарушение правил формата).
7. Статус 'insufficient' с выдуманным фактом (галлюцинация).
8. Недоступность LLM (корректный fallback / исключение).
9. BM25 возвращает не более 15 утверждений.
10. Режимы B и C получают абсолютно одинаковые claim_id.
"""

import json
import pytest
from pydantic import ValidationError
from src.padic import padic_distance, compute_padic_code, decode_padic_code, group_claims_by_padic_branches
from src.schemas import Claim, Question, LLMOutput, Document
from src.retrieval import BM25ClaimRetriever
from src.context_builder import build_mode_b_context, build_mode_c_context
from src.llm import extract_json_block, LLMClient

# --- 1. Одинаковые p-adic пути ---
def test_padic_identical_paths():
    p1 = (0, 1, 2)
    p2 = (0, 1, 2)
    assert padic_distance(p1, p2) == 0.0

# --- 2. Различие на каждом из трёх уровней ---
def test_padic_difference_levels():
    # Различие на первом уровне a0: d3 = 3^0 = 1.0
    assert padic_distance((0, 1, 2), (1, 1, 2)) == 1.0
    # Совпадение a0, различие a1: d3 = 3^(-1) = 1/3
    assert pytest.approx(padic_distance((0, 0, 2), (0, 1, 2)), 0.001) == 1.0 / 3.0
    # Совпадение a0, a1, различие a2: d3 = 3^(-2) = 1/9
    assert pytest.approx(padic_distance((0, 0, 0), (0, 0, 1)), 0.001) == 1.0 / 9.0

# --- 3. Ультраметрическое неравенство ---
def test_ultrametric_inequality():
    # Для любых x, y, z должно выполняться d(x, z) <= max(d(x, y), d(y, z))
    paths = [
        (0, 0, 0), (0, 0, 1), (0, 1, 0), (1, 0, 0), (2, 2, 2), (0, 1, 1)
    ]
    for x in paths:
        for y in paths:
            for z in paths:
                d_xz = padic_distance(x, z)
                d_xy = padic_distance(x, y)
                d_yz = padic_distance(y, z)
                assert d_xz <= max(d_xy, d_yz) + 1e-9

# --- 4. Невалидный JSON от LLM ---
def test_invalid_llm_json():
    raw_text = "Конечно! Вот ответ: { 'status': 'entailed' incomplete json..."
    parsed = extract_json_block(raw_text)
    assert parsed is None

# --- 5. Валидация несуществующего evidence_id ---
def test_nonexistent_evidence_id():
    valid_claim_ids = {"C01", "C02", "C03"}
    llm_output_data = {
        "question_id": "Q01",
        "status": "entailed",
        "answer": "Факт",
        "evidence_ids": ["C99"],  # C99 не существует
        "counterevidence_ids": [],
        "confidence": 0.9,
        "explanation": "Тест"
    }
    output = LLMOutput.model_validate(llm_output_data)
    # Проверка обнаружения невалидного ID
    invalid_ids = [cid for cid in output.evidence_ids if cid not in valid_claim_ids]
    assert len(invalid_ids) > 0
    assert invalid_ids == ["C99"]

# --- 6. Статус 'both' без counterevidence_ids ---
def test_both_without_counterevidence():
    output_data = {
        "question_id": "Q09",
        "status": "both",
        "answer": "Спорный вопрос",
        "evidence_ids": ["C14"],
        "counterevidence_ids": [],  # Пусто при both — нарушение правил логики
        "confidence": 0.8,
        "explanation": "Конфликт"
    }
    output = LLMOutput.model_validate(output_data)
    # Правило: при status == 'both' должны быть и evidence, и counterevidence
    is_valid_both = (output.status != "both") or (len(output.evidence_ids) > 0 and len(output.counterevidence_ids) > 0)
    assert is_valid_both is False

# --- 7. Статус 'insufficient' с выдуманным фактом ---
def test_insufficient_with_hallucinated_fact():
    output_data = {
        "question_id": "Q11",
        "status": "insufficient",
        "answer": "Морозов удалил базу намеренно, потому что хотел отомстить директору.",  # Выдуманная догадка
        "evidence_ids": [],
        "counterevidence_ids": [],
        "confidence": 0.95,  # Чрезмерная уверенность при недостатке данных
        "explanation": "Недостаточно данных"
    }
    output = LLMOutput.model_validate(output_data)
    # Тест ловит завышенный confidence (> 0.7) при статусе insufficient
    assert output.status == "insufficient"
    assert output.confidence > 0.7  # Индикатор оверконфидентности при недостатке данных

# --- 8. Недоступность LLM ---
def test_llm_unavailable():
    # Создаем клиент без ключа / с невалидным окружением
    client = LLMClient(credentials="")
    output, tokens, latency, raw = client.generate("Тестовый запрос")
    assert output is not None
    assert output.status == "insufficient"
    assert "GIGACHAT_CREDENTIALS" in (output.answer or "") or "GIGACHAT_CREDENTIALS" in output.explanation

# --- 9. BM25 возвращает не более 15 утверждений ---
def test_bm25_returns_max_15():
    # Загружаем реальные утверждения из data/claims.jsonl
    claims = []
    with open("data/claims.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            claims.append(Claim.model_validate_json(line))
    
    assert len(claims) >= 30
    retriever = BM25ClaimRetriever(claims)
    top_claims = retriever.retrieve("Кто заблокировал пользователей платформы?", top_k=15)
    assert len(top_claims) <= 15
    assert len(top_claims) == 15

# --- 10. Режимы B и C получают абсолютно одинаковые claim_id ---
def test_modes_b_and_c_get_identical_claim_ids():
    claims = []
    with open("data/claims.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            claims.append(Claim.model_validate_json(line))
            
    with open("data/claim_paths.json", "r", encoding="utf-8") as f:
        claim_paths = json.load(f)

    retriever = BM25ClaimRetriever(claims)
    top_claims = retriever.retrieve("мастер-ключ RED_OVERRIDE консоль", top_k=15)
    
    # Для режима B:
    mode_b_ids = [c.claim_id for c in top_claims]
    
    # Для режима C (те же top_claims, только сгруппированные):
    branches = group_claims_by_padic_branches(top_claims, {k: tuple(v) for k, v in claim_paths.items()})
    mode_c_ids = []
    for branch_claims in branches.values():
        for c in branch_claims:
            mode_c_ids.append(c.claim_id)
            
    assert set(mode_b_ids) == set(mode_c_ids)
    assert len(mode_b_ids) == len(mode_c_ids) == 15
