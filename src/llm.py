import os, json, re, time, uuid, requests
from typing import Optional, Dict, Any, Tuple, List
from dotenv import load_dotenv
from src.schemas import LLMOutput

load_dotenv()

SYSTEM_PROMPT = """Ты — беспристрастный AI-детектив и аналитик фактов. Отвечай СТРОГО по контексту.
СТАТУСЫ (status):
- "entailed": следует из данных.
- "contradicted": опровергается данными.
- "both": конфликт источников (заполни evidence_ids и counterevidence_ids).
- "insufficient": недостаточно данных, не строй догадок. Укажи нехватку в explanation.

ВЕРНИ ТОЛЬКО JSON:
{"question_id": "...", "status": "entailed|contradicted|both|insufficient", "answer": "...", "evidence_ids": ["C01"], "counterevidence_ids": [], "confidence": 0.85, "explanation": "..."}
Идентификаторы Cxx бери строго из контекста."""

def extract_json_block(text: str) -> Optional[dict]:
    for pattern in [r"```(?:json)?\s*(\{.*?\})\s*```", r"(\{.*\})"]:
        m = re.search(pattern, text, re.DOTALL)
        if m:
            try: return json.loads(m.group(1))
            except Exception: pass
    try: return json.loads(text.strip())
    except Exception: return None

class LLMClient:
    AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    API_URL = "https://gigachat.devices.sberbank.ru/api/v1"

    def __init__(self, credentials: Optional[str] = None, model: str = "GigaChat", scope: str = "GIGACHAT_API_PERS"):
        self.credentials = credentials.strip() if credentials is not None else os.getenv("GIGACHAT_CREDENTIALS", "").strip()
        self.model = model
        self.scope = scope or os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
        self.token = None

    def get_token(self) -> str:
        if self.token: return self.token
        if self.credentials.startswith("ey") and len(self.credentials) > 100:
            self.token = self.credentials
            return self.token
        r = requests.post(self.AUTH_URL, headers={"Authorization": f"Basic {self.credentials}", "RqUID": str(uuid.uuid4())},
                          data={"scope": self.scope}, verify=False, timeout=15)
        if r.status_code != 200: raise RuntimeError(f"Auth error ({r.status_code}): {r.text}")
        self.token = r.json().get("access_token")
        return self.token

    def get_available_models(self) -> Tuple[List[str], Optional[str]]:
        try:
            r = requests.get(f"{self.API_URL}/models", headers={"Authorization": f"Bearer {self.get_token()}"}, verify=False, timeout=15)
            if r.status_code == 200:
                return [m["id"] for m in r.json().get("data", []) if "id" in m], None
            return [], f"HTTP {r.status_code}: {r.text}"
        except Exception as e:
            return [], str(e)

    def generate(self, user_prompt: str, system_prompt: str = SYSTEM_PROMPT) -> Tuple[Optional[LLMOutput], int, float, str]:
        t0 = time.time()
        if not self.credentials:
            out = LLMOutput(question_id="MOCK", status="insufficient", answer="Отсутствуют GIGACHAT_CREDENTIALS", confidence=0.5, explanation="GIGACHAT_CREDENTIALS не заданы.")
            return out, 50, time.time() - t0, json.dumps(out.model_dump())

        models, _ = self.get_available_models()
        target = self.model if (models and self.model in models) else (models[0] if models else "GigaChat")

        try:
            token = self.get_token()
            payload = {"model": target, "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], "temperature": 0.01, "max_tokens": 1000}
            r = requests.post(f"{self.API_URL}/chat/completions", headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}, json=payload, verify=False, timeout=60)
            
            # Авто-fallback при 404
            if r.status_code == 404:
                for alt in ["GigaChat-2", "GigaChat:latest", "GigaChat-Pro"]:
                    if alt != target:
                        payload["model"] = alt
                        r = requests.post(f"{self.API_URL}/chat/completions", headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}, json=payload, verify=False, timeout=60)
                        if r.status_code == 200: break
            
            if r.status_code != 200: raise RuntimeError(f"GigaChat API ({r.status_code}): {r.text}")

            res = r.json()
            content = res["choices"][0]["message"]["content"]
            tokens = res.get("usage", {}).get("total_tokens", len(content.split()) * 2)
            parsed = extract_json_block(content) or {}
            return LLMOutput.model_validate(parsed), tokens, time.time() - t0, content
        except Exception as e:
            out = LLMOutput(question_id="ERR", status="insufficient", answer=f"Сбой: {e}", confidence=0.5, explanation=f"Недоступность LLM: {e}")
            return out, 50, time.time() - t0, json.dumps(out.model_dump())
