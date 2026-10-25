import os
import json
import re
import time
from typing import Optional, Dict, Any, Tuple, List
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
    try:
        return json.loads(text.strip())
    except Exception:
        pass
    
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
    def __init__(self, credentials: Optional[str] = None, model: str = "GigaChat", scope: str = "GIGACHAT_API_PERS"):
        self.credentials = credentials or os.getenv("GIGACHAT_CREDENTIALS")
        self.model = model
        self.scope = scope or os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
        self.client = None
        if self.credentials:
            try:
                from gigachat import GigaChat
                self.client = GigaChat(
                    credentials=self.credentials,
                    scope=self.scope,
                    verify_ssl_certs=False,
                    model=self.model,
                    timeout=60
                )
            except Exception as e:
                print(f"[Warning] Ошибка инициализации GigaChat: {e}")

    def get_available_models(self) -> List[str]:
        if not self.client:
            return []
        try:
            models_resp = self.client.get_models()
            return [m.id for m in models_resp.data]
        except Exception as e:
            print(f"[Warning] Не удалось получить список моделей: {e}")
            return []

    def generate(self, user_prompt: str, system_prompt: str = SYSTEM_PROMPT) -> Tuple[Optional[LLMOutput], int, float, str]:
        start_time = time.time()
        
        if not self.client:
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

        # Определяем рабочую модель
        target_model = self.model
        available = self.get_available_models()
        if available:
            if target_model not in available:
                # Если запрошенной модели нет, берем первую доступную
                target_model = available[0]

        try:
            from gigachat.models import Chat, Messages, MessagesRole
            payload = Chat(
                model=target_model,
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
                raise ValueError(f"Не удалось извлечь JSON из ответа модели:\n{content}")
            
            output = LLMOutput.model_validate(parsed_json)
            return output, tokens, latency, content
        except Exception as e:
            latency = time.time() - start_time
            err_msg = str(e)
            if "No such model" in err_msg or "404" in err_msg:
                # Дополнительная информативная подсказка по доступным моделям
                hint = f" Запрошенная модель: '{target_model}'."
                if available:
                    hint += f" Доступные модели для данного токена: {available}."
                else:
                    hint += " Проверьте тип учетной записи (Физлицо: GIGACHAT_API_PERS или Юрлицо: GIGACHAT_API_CORP)."
                raise RuntimeError(f"Модель недоступна: {err_msg}.{hint}")
            raise RuntimeError(f"Ошибка вызова GigaChat: {e}")
