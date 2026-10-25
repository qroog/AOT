import os
import json
import re
import time
from typing import Optional, Dict, Any, Tuple
from dotenv import load_dotenv
from src.schemas import LLMOutput

load_dotenv()

SYSTEM_PROMPT = """Ты — беспристрастный AI-детектив и аналитик фактов.
Твоя задача — отвечать на вопросы СТРОГО на основе предоставленного контекста.

ПРАВИЛА ОЦЕНКИ СТАТУСА (status):
- "entailed": утверждение однозначно следует из предоставленных данных.
- "contradicted": утверждение однозначно опровергается предоставленными данными.
- "both": в данных есть ОБА типа оснований — и подтверждающие, и опровергающие (конфликт источников). В этом случае ОБЯЗАТЕЛЬНО заполни и evidence_ids, и counterevidence_ids.
- "insufficient": данных недостаточно для однозначного вывода, граница между фактом и догадкой. Не строй догадок! В поле explanation укажи, какой именно информации не хватает.

ТРЕБОВАНИЯ К ФОРМАТУ ОТВЕТА:
Верни ТОЛЬКО валидный JSON-объект следующей структуры:
{
  "question_id": "<id вопроса>",
  "status": "entailed | contradicted | both | insufficient",
  "answer": "Краткий ответ по существу или null",
  "evidence_ids": ["C01", "C02"],
  "counterevidence_ids": ["C05"],
  "confidence": 0.85,
  "explanation": "Краткая проверяемая связь между доказательствами"
}
Важно: Все идентификаторы в evidence_ids и counterevidence_ids ДОЛЖНЫ быть взяты из предоставленных утверждений (например C01, C02).
"""

def extract_json_block(text: str) -> Optional[dict]:
    # Попытка прямого распарсивания
    try:
        return json.loads(text.strip())
    except Exception:
        pass
    
    # Поиск ```json ... ``` или {...}
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass
            
    match2 = re.search(r"(\{.*\})", text, re.DOTALL)
    if match2:
        try:
            return json.loads(match2.group(1))
        except Exception:
            pass
    return None

class LLMClient:
    def __init__(self, credentials: Optional[str] = None, model: str = "GigaChat"):
        self.credentials = credentials or os.getenv("GIGACHAT_CREDENTIALS")
        self.model = model
        self.client = None
        if self.credentials:
            try:
                from gigachat import GigaChat
                self.client = GigaChat(
                    credentials=self.credentials,
                    verify_ssl_certs=False,
                    model=self.model,
                    timeout=60
                )
            except Exception as e:
                print(f"[Warning] GigaChat client init error: {e}")

    def generate(self, user_prompt: str, system_prompt: str = SYSTEM_PROMPT) -> Tuple[Optional[LLMOutput], int, float, str]:
        """
        Возвращает (LLMOutput, token_count, latency_seconds, raw_response)
        """
        start_time = time.time()
        
        if not self.client:
            # Fallback для тестов и оффлайн-режима
            latency = time.time() - start_time
            mock_out = LLMOutput(
                question_id="MOCK",
                status="insufficient",
                answer="Отсутствуют учетные данные GIGACHAT_CREDENTIALS",
                evidence_ids=[],
                counterevidence_ids=[],
                confidence=0.5,
                explanation="Клиент GigaChat не инициализирован. Задайте ключ в .env или в интерфейсе."
            )
            return mock_out, 50, latency, json.dumps(mock_out.model_dump())

        try:
            from gigachat.models import Chat, Messages, MessagesRole
            payload = Chat(
                messages=[
                    Messages(role=MessagesRole.SYSTEM, content=system_prompt),
                    Messages(role=MessagesRole.USER, content=user_prompt)
                ],
                temperature=0.01,
                max_tokens=1000
            )
            res = self.client.chat(payload)
            content = res.choices[0].message.content
            latency = time.time() - start_time
            tokens = getattr(res.usage, "total_tokens", len(content.split()) * 2) if hasattr(res, "usage") else 100
            
            parsed_json = extract_json_block(content)
            if not parsed_json:
                raise ValueError(f"Не удалось извлечь JSON из ответа модели: {content}")
            
            output = LLMOutput.model_validate(parsed_json)
            return output, tokens, latency, content
        except Exception as e:
            latency = time.time() - start_time
            raise RuntimeError(f"Ошибка вызова GigaChat: {e}")
