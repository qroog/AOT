import os
import json
import re
import time
import uuid
import requests
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

def fetch_gigachat_models(credentials: str, scope: str = "GIGACHAT_API_PERS") -> Tuple[List[str], Optional[str]]:
    """
    Прямой запрос токена и списка моделей к API GigaChat.
    Возвращает (список моделей, текст ошибки).
    """
    creds = credentials.strip()
    if not creds:
        return [], "Credentials не указаны."

    # Если уже передан bearer access token
    if creds.startswith("ey") and len(creds) > 100:
        token = creds
    else:
        # Получаем access token через OAuth
        auth_url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        headers = {
            "Authorization": f"Basic {creds}",
            "RqUID": str(uuid.uuid4()),
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"scope": scope}
        try:
            r = requests.post(auth_url, headers=headers, data=data, verify=False, timeout=15)
            if r.status_code != 200:
                return [], f"Ошибка авторизации ({r.status_code}): {r.text}"
            token = r.json().get("access_token")
            if not token:
                return [], f"Не удалось извлечь токен: {r.text}"
        except Exception as e:
            return [], f"Ошибка соединения с сервером авторизации Сбера: {e}"

    # Запрашиваем модели
    models_url = "https://gigachat.devices.sberbank.ru/api/v1/models"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    try:
        r_models = requests.get(models_url, headers=headers, verify=False, timeout=15)
        if r_models.status_code != 200:
            return [], f"Ошибка получения моделей ({r_models.status_code}): {r_models.text}"
        data = r_models.json().get("data", [])
        model_ids = [m["id"] for m in data if "id" in m]
        return model_ids, None
    except Exception as e:
        return [], f"Ошибка запроса моделей: {e}"


class LLMClient:
    def __init__(self, credentials: Optional[str] = None, model: str = "GigaChat", scope: str = "GIGACHAT_API_PERS"):
        if credentials is not None:
            self.credentials = credentials.strip()
        else:
            self.credentials = os.getenv("GIGACHAT_CREDENTIALS", "").strip()
        self.model = model
        self.scope = scope or os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
        self.access_token = None

    def get_token(self) -> str:
        if self.access_token:
            return self.access_token
        if self.credentials.startswith("ey") and len(self.credentials) > 100:
            self.access_token = self.credentials
            return self.access_token
        
        auth_url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        headers = {
            "Authorization": f"Basic {self.credentials}",
            "RqUID": str(uuid.uuid4()),
            "Content-Type": "application/x-www-form-urlencoded"
        }
        r = requests.post(auth_url, headers=headers, data={"scope": self.scope}, verify=False, timeout=20)
        if r.status_code != 200:
            raise RuntimeError(f"Ошибка получения токена Сбера ({r.status_code}): {r.text}")
        self.access_token = r.json().get("access_token")
        return self.access_token

    def get_available_models(self) -> Tuple[List[str], Optional[str]]:
        return fetch_gigachat_models(self.credentials, self.scope)

    def generate(self, user_prompt: str, system_prompt: str = SYSTEM_PROMPT) -> Tuple[Optional[LLMOutput], int, float, str]:
        start_time = time.time()
        
        if not self.credentials:
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
            available_models, _ = self.get_available_models()
        except Exception:
            available_models = []

        target_model = self.model
        if available_models:
            if target_model not in available_models:
                target_model = available_models[0]
        else:
            if target_model == "Авто-выбор доступной" or not target_model:
                target_model = "GigaChat"

        try:
            token = self.get_token()
            chat_url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": target_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.01,
                "max_tokens": 1000
            }

            # Отправляем запрос
            r = requests.post(chat_url, headers=headers, json=payload, verify=False, timeout=60)
            latency = time.time() - start_time
            
            if r.status_code != 200:
                err_text = r.text
                if "No such model" in err_text or r.status_code == 404:
                    alt_models = ["GigaChat-2", "GigaChat:latest", "GigaChat-Pro", "GigaChat"]
                    for alt in alt_models:
                        if alt != target_model:
                            payload["model"] = alt
                            r_alt = requests.post(chat_url, headers=headers, json=payload, verify=False, timeout=60)
                            if r_alt.status_code == 200:
                                r = r_alt
                                break
                
                if r.status_code != 200:
                    raise RuntimeError(f"GigaChat API ({r.status_code}): {r.text} | Модель: '{target_model}'")

            res_json = r.json()
            content = res_json["choices"][0]["message"]["content"]
            usage = res_json.get("usage", {})
            tokens = usage.get("total_tokens", len(content.split()) * 2)

            parsed_json = extract_json_block(content)
            if not parsed_json:
                raise ValueError(f"Не удалось извлечь JSON из ответа модели:\n{content}")
            
            output = LLMOutput.model_validate(parsed_json)
            return output, tokens, latency, content
        except Exception as e:
            latency = time.time() - start_time
            mock_out = LLMOutput(
                question_id="CONN_ERR",
                status="insufficient",
                answer=f"Ошибка соединения / недоступность LLM: {e}",
                evidence_ids=[],
                counterevidence_ids=[],
                confidence=0.5,
                explanation=f"Сетевой сбой или недоступность сервера GigaChat: {e}"
            )
            return mock_out, 50, latency, json.dumps(mock_out.model_dump())
