import asyncio
import json
import httpx
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OLLAMA_HOST, OLLAMA_MODEL, OLLAMA_API_KEY


class OllamaClient:
    """Dual-connection Ollama client: REST API (Cloud / remote) + library (local)."""

    def __init__(self):
        self.model = OLLAMA_MODEL
        self.host = OLLAMA_HOST
        self.api_key = OLLAMA_API_KEY
        self._use_library = None
        self._checked = False

    def set_model(self, model_name: str):
        self.model = model_name

    def _get_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def check_connection(self) -> dict:
        status = {
            "library": False,
            "rest": False,
            "model": self.model,
            "cloud": bool(self.api_key or "ollama.com" in self.host),
            "available_models": []
        }

        # If API key is present or host points to ollama.com, prioritize REST with auth
        if self.api_key or "ollama.com" in self.host:
            try:
                headers = self._get_headers()
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(f"{self.host}/api/tags", headers=headers)
                    if resp.status_code == 200:
                        status["rest"] = True
                        data = resp.json()
                        models = []
                        for m in data.get("models", []):
                            name = m.get("name", m.get("model", ""))
                            if name:
                                models.append(name)
                        status["available_models"] = models
                        self._use_library = False
                        self._checked = True
                        return status
                    else:
                        status["rest_error"] = f"HTTP {resp.status_code}: {resp.text[:200]}"
            except Exception as e:
                status["rest_error"] = str(e)

        # Try ollama library (local Ollama)
        try:
            import ollama as _ollama
            client = _ollama.Client(host=self.host, headers=self._get_headers())
            result = await asyncio.to_thread(client.list)
            status["library"] = True
            models = []
            model_list = result.get("models", []) if isinstance(result, dict) else (result.models if hasattr(result, "models") else [])
            for m in model_list:
                name = m.get("name", m.get("model", "")) if isinstance(m, dict) else (m.name if hasattr(m, "name") else str(m))
                models.append(name)
            status["available_models"] = models
        except Exception as e:
            status["library_error"] = str(e)

        # Fallback REST API check
        if not status["rest"]:
            try:
                headers = self._get_headers()
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(f"{self.host}/api/tags", headers=headers)
                    if resp.status_code == 200:
                        status["rest"] = True
                        data = resp.json()
                        models = [m.get("name", m.get("model", "")) for m in data.get("models", []) if m.get("name") or m.get("model")]
                        if models:
                            status["available_models"] = models
            except Exception as e:
                status["rest_error"] = str(e)

        if status["rest"]:
            self._use_library = False
        elif status["library"]:
            self._use_library = True
        else:
            self._use_library = None

        self._checked = True
        return status

    async def _ensure_checked(self):
        if not self._checked:
            await self.check_connection()

    async def generate(self, prompt: str, system: str = "",
                       messages: list = None, stream: bool = True):
        await self._ensure_checked()

        if messages is None:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

        if self._use_library is False:
            async for chunk in self._rest_generate(messages, stream):
                yield chunk
        elif self._use_library is True:
            async for chunk in self._library_generate(messages, stream):
                yield chunk
        else:
            yield "[ERROR] Ollama not available. Check your OLLAMA_API_KEY and connection."

    async def _library_generate(self, messages, stream):
        import ollama as _ollama
        client = _ollama.Client(host=self.host, headers=self._get_headers())
        try:
            if stream:
                gen = await asyncio.to_thread(
                    lambda: client.chat(model=self.model, messages=messages, stream=True)
                )
                for chunk in gen:
                    content = ""
                    if hasattr(chunk, "message"):
                        msg = chunk.message
                        content = msg.content if hasattr(msg, "content") else msg.get("content", "")
                    elif isinstance(chunk, dict):
                        content = chunk.get("message", {}).get("content", "")
                    if content:
                        yield content
            else:
                response = await asyncio.to_thread(
                    lambda: client.chat(model=self.model, messages=messages, stream=False)
                )
                if hasattr(response, "message"):
                    msg = response.message
                    yield msg.content if hasattr(msg, "content") else msg.get("content", "")
                elif isinstance(response, dict):
                    yield response.get("message", {}).get("content", "")
        except Exception as e:
            print(f"[LLM] Library error, falling back to REST: {e}")
            self._use_library = False
            async for chunk in self._rest_generate(messages, stream):
                yield chunk

    async def _rest_generate(self, messages, stream):
        url = f"{self.host}/api/chat"
        payload = {"model": self.model, "messages": messages, "stream": stream}
        headers = self._get_headers()
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                if stream:
                    async with client.stream("POST", url, json=payload, headers=headers) as resp:
                        if resp.status_code != 200:
                            err_body = await resp.aread()
                            yield f"[ERROR] Ollama Cloud HTTP {resp.status_code}: {err_body.decode(errors='replace')}"
                            return
                        async for line in resp.aiter_lines():
                            if line.strip():
                                try:
                                    data = json.loads(line)
                                    content = data.get("message", {}).get("content", "")
                                    if content:
                                        yield content
                                except json.JSONDecodeError:
                                    continue
                else:
                    resp = await client.post(url, json=payload, headers=headers)
                    if resp.status_code != 200:
                        yield f"[ERROR] Ollama Cloud HTTP {resp.status_code}: {resp.text}"
                        return
                    data = resp.json()
                    yield data.get("message", {}).get("content", "")
        except Exception as e:
            yield f"[ERROR] Ollama REST failed: {e}"

    async def generate_oneshot(self, prompt: str, system: str = "",
                               messages: list = None) -> str:
        result = []
        async for chunk in self.generate(prompt, system, messages, stream=False):
            result.append(chunk)
        return "".join(result)


ollama_client = OllamaClient()
