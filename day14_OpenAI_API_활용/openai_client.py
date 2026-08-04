# [제공 코드] 이 파일은 실습 환경을 굴러가게 하는 장치입니다 — 수업 내용이 아니며 열어 볼 필요 없습니다.
"""실습용 OpenAI 클라이언트 — 키가 있으면 실제 API, 없으면 저장해 둔 응답으로 재생한다.

노트북에서 쓰는 것은 `get_client()` 하나뿐이고, 돌려주는 client 의 사용법은
공식 문서와 완전히 같다(아래 두 메서드가 오늘 배우는 전부다).

    client.chat.completions.create(...)   # Chat Completions
    client.responses.create(...)          # Responses

- 텍스트 생성 가이드 : https://developers.openai.com/api/docs/guides/text
- Chat Completions 레퍼런스 : https://developers.openai.com/api/docs/api-reference/chat

이 파일 안의 `_` 로 시작하는 함수들은 **키 없이도 수업이 굴러가게 하는 장치**다
(요청을 지문으로 바꿔 저장된 응답을 찾아 준다). 수업 내용과는 무관하니 열어 볼 필요 없다.
"""
import os
import json
import hashlib
from pathlib import Path
from types import SimpleNamespace

from dotenv import load_dotenv

load_dotenv(".env")       # 같은 폴더의 .env
load_dotenv("../.env")    # 정답 폴더에서 실행하는 경우

_DATA_DIR = Path("data") if Path("data").exists() else Path("../data")
_CACHE_FILE = _DATA_DIR / "api_cache.json"
_CACHE = json.loads(_CACHE_FILE.read_text(encoding="utf-8")) if _CACHE_FILE.exists() else {}
_REPLAY_POS = {}
_HAS_KEY = bool(os.getenv("OPENAI_API_KEY"))

def _norm_tools(tools):
    """도구는 이름·파라미터만 캐시 키에 반영한다(자유 서술 description 은 제외 — 같은 함수면 재현)."""
    if not tools:
        return tools
    out = []
    for t in tools:
        fn = t.get("function", {}) if isinstance(t, dict) else {}
        out.append({"type": t.get("type"), "name": fn.get("name"), "parameters": fn.get("parameters")})
    return out

def _norm_rf(rf):
    """구조화 출력 스키마를 캐시 키에 안정적으로 반영한다(pydantic 모델은 JSON 스키마로 바꾼다)."""
    if rf is not None and hasattr(rf, "model_json_schema"):
        try:
            return rf.model_json_schema()
        except Exception:
            return getattr(rf, "__name__", str(rf))
    return rf

def _norm_messages(messages):
    """캐시 키에서 tool_call 의 id 를 지운다.

    ⚠️ Function Calling 은 보통 2회 호출이다(도구 요청 → 우리가 실행 → 결과를 담아 재호출).
    재호출 메시지에는 OpenAI 가 매번 새로 만드는 `tool_call.id` 가 들어간다.
    이 id 를 키에 넣으면 **실제 호출 때의 id 와 오프라인 재생 때의 id 가 달라져
    재호출만 캐시 미스**가 나고, 학생 화면에 폴백 문구가 뜬다(실측 확인).
    id 는 응답 내용과 무관하므로 키에서 제외한다.
    """
    if not isinstance(messages, list):
        return messages
    out = []
    for m in messages:
        if not isinstance(m, dict):
            out.append(m)
            continue
        m2 = {k: v for k, v in m.items() if k != "tool_call_id"}
        if isinstance(m2.get("tool_calls"), list):
            m2["tool_calls"] = [
                {k: v for k, v in (tc or {}).items() if k != "id"} if isinstance(tc, dict) else tc
                for tc in m2["tool_calls"]]
        out.append(m2)
    return out


def _fingerprint(kind, kwargs):
    """모델·메시지·주요 파라미터로 응답을 재현할 캐시 키를 만든다."""
    keep = {k: kwargs.get(k) for k in (
        "model", "input", "temperature", "top_p",
        "max_tokens", "max_completion_tokens", "reasoning_effort", "tool_choice")}
    keep["messages"] = _norm_messages(kwargs.get("messages"))
    keep["tools"] = _norm_tools(kwargs.get("tools"))
    keep["response_format"] = _norm_rf(kwargs.get("response_format"))
    blob = json.dumps([kind, keep], ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()[:20]

def _next_pos(fp):
    pos = _REPLAY_POS.get(fp, 0)
    _REPLAY_POS[fp] = pos + 1
    return pos

def _example_for_annotation(ann):
    """파이썬 타입 힌트를 보고 오프라인 폴백용 예시 값을 만든다(pydantic .parse 폴백)."""
    import typing
    from pydantic import BaseModel
    origin = typing.get_origin(ann)
    args = typing.get_args(ann)
    if origin is typing.Literal:
        return args[0]
    if type(None) in args:            # Optional[X] — 비워 두는 것이 안전한 폴백이다
        return None
    if origin in (list, typing.List):
        inner = args[0] if args else str
        return [_example_for_annotation(inner)]
    if isinstance(ann, type) and issubclass(ann, BaseModel):
        return {n: _example_for_annotation(f.annotation) for n, f in ann.model_fields.items()}
    if ann is float:
        return 0.0
    if ann is int:
        return 0
    if ann is bool:
        return False
    return "(오프라인 예시)"

def _pyd_example(model):
    if model is None:
        return {}
    return {n: _example_for_annotation(f.annotation) for n, f in model.model_fields.items()}

def _replay_parse(fp, rf):
    bucket = _CACHE.get(fp)
    data = bucket[_next_pos(fp) % len(bucket)]["parsed"] if bucket else _pyd_example(rf)
    parsed = rf.model_validate(data) if rf is not None and hasattr(rf, "model_validate") else data
    msg = SimpleNamespace(parsed=parsed, content=json.dumps(data, ensure_ascii=False, default=str))
    usage = _wrap({"total_tokens": 0, "prompt_tokens": 0, "completion_tokens": 0,
                   "completion_tokens_details": {"reasoning_tokens": 0}})
    return SimpleNamespace(choices=[SimpleNamespace(message=msg)], usage=usage)

def _dump_parse(resp):
    parsed = resp.choices[0].message.parsed
    return {"parsed": parsed.model_dump() if hasattr(parsed, "model_dump") else parsed}

def _last_user_text(kwargs):
    text = ""
    if isinstance(kwargs.get("input"), str):
        text = kwargs["input"]
    for m in kwargs.get("messages") or []:
        if isinstance(m, dict) and m.get("role") == "user" and isinstance(m.get("content"), str):
            text = m["content"]
    return text

def _schema_example(schema):
    """JSON 스키마를 만족하는 최소 예시 객체를 만든다(오프라인 폴백용)."""
    out = {}
    for key, spec in (schema.get("properties") or {}).items():
        if "enum" in spec:
            out[key] = spec["enum"][0]
        elif spec.get("type") == "string":
            out[key] = "(오프라인 예시)"
        elif spec.get("type") in ("number", "integer"):
            out[key] = 0
        elif spec.get("type") == "array":
            out[key] = []
        elif spec.get("type") == "boolean":
            out[key] = False
        elif spec.get("type") == "object":
            out[key] = _schema_example(spec)
        else:
            out[key] = None
    return out

def _example_args(parameters, kwargs):
    """도구 파라미터 스키마에 맞는 인자를 사용자 메시지에서 최대한 뽑아 만든다(폴백용)."""
    import re
    text = _last_user_text(kwargs)
    args = {}
    for key, spec in (parameters.get("properties") or {}).items():
        if spec.get("type") in ("integer", "number"):
            nums = re.findall(r"\d+", text)
            args[key] = int(nums[0]) if nums else 1
        elif spec.get("type") == "string":
            args[key] = (text.strip()[:10] or "예시")
        else:
            args[key] = None
    return args

def _fallback(kind, kwargs):
    """캐시에 없을 때 요청 형태에 맞는 안전한 응답을 만든다(어떤 코드든 크래시하지 않게)."""
    usage = {"total_tokens": 0, "prompt_tokens": 0, "completion_tokens": 0,
             "completion_tokens_details": {"reasoning_tokens": 0}}
    if kind == "response":
        return _wrap({"output_text": "(오프라인 예시 응답입니다)"})
    rf = kwargs.get("response_format")
    if isinstance(rf, dict) and rf.get("type") == "json_schema":
        obj = _schema_example(rf["json_schema"]["schema"])
        content = json.dumps(obj, ensure_ascii=False)
        return _wrap({"choices": [{"message": {"content": content, "tool_calls": None}}], "usage": usage})
    tools = kwargs.get("tools")
    if tools:
        fn = tools[0]["function"]
        args = _example_args(fn.get("parameters") or {}, kwargs)
        tool_calls = [{"id": "call_offline", "type": "function",
                       "function": {"name": fn["name"], "arguments": json.dumps(args, ensure_ascii=False)}}]
        return _wrap({"choices": [{"message": {"content": None, "tool_calls": tool_calls}}], "usage": usage})
    return _wrap({"choices": [{"message": {"content": "(오프라인 예시 응답입니다)", "tool_calls": None}}], "usage": usage})

def _wrap(value):
    """딕셔너리를 점(.)으로 접근할 수 있는 객체로 감싼다(캐시 응답 재구성용)."""
    if isinstance(value, dict):
        return SimpleNamespace(**{k: _wrap(v) for k, v in value.items()})
    if isinstance(value, list):
        return [_wrap(v) for v in value]
    return value

def _save_cache():
    try:
        _CACHE_FILE.write_text(json.dumps(_CACHE, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception:
        pass

def _remember(fp, dumped):
    bucket = _CACHE.setdefault(fp, [])
    if dumped not in bucket:
        bucket.append(dumped)
    # 같은 요청은 3개까지만 저장한다(온도 실험용). **앞에서 자르지 않는 것이 중요하다** —
    # 오프라인 재생은 bucket[0] 부터 쓰므로, 첫 항목이 바뀌면 그 값으로 만든 다음 프롬프트가
    # 통째로 캐시 미스가 된다(리포트 생성처럼 앞 결과를 프롬프트에 넣는 단계에서 실제로 발생).
    del bucket[3:]
    _save_cache()

def _replay(kind, fp, kwargs):
    bucket = _CACHE.get(fp)
    if not bucket:
        return _fallback(kind, kwargs)      # 캐시에 없으면 요청 형태에 맞는 안전한 응답
    pos = _REPLAY_POS.get(fp, 0)
    _REPLAY_POS[fp] = pos + 1
    return _wrap(bucket[pos % len(bucket)])

def _dump_chat(resp):
    msg = resp.choices[0].message
    tool_calls = None
    if getattr(msg, "tool_calls", None):
        tool_calls = [{"id": t.id, "type": "function",
                       "function": {"name": t.function.name, "arguments": t.function.arguments}}
                      for t in msg.tool_calls]
    usage = resp.usage
    details = getattr(usage, "completion_tokens_details", None)
    reasoning = getattr(details, "reasoning_tokens", 0) or 0
    return {"choices": [{"message": {"content": msg.content, "tool_calls": tool_calls}}],
            "usage": {"total_tokens": usage.total_tokens, "prompt_tokens": usage.prompt_tokens,
                      "completion_tokens": usage.completion_tokens,
                      "completion_tokens_details": {"reasoning_tokens": reasoning}}}

def _dump_response(resp):
    return {"output_text": resp.output_text}

def _chunk(text):
    return SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=text))])


def _call_live(fn, **kwargs):
    """실제 호출. 분당 토큰 제한(429)에 걸리면 잠시 쉬었다 다시 시도한다.

    이미지 요청은 한 번에 수만 토큰을 쓰기 때문에 여러 장을 연달아 보내면 쉽게 걸린다.
    """
    import time
    delay = 20
    for attempt in range(6):
        try:
            return fn(**kwargs)
        except Exception as e:
            if type(e).__name__ != "RateLimitError" or attempt == 5:
                raise
            print(f"  (분당 토큰 제한 — {delay}초 쉬었다 재시도 {attempt + 1}/5)")
            time.sleep(delay)
            delay = min(delay * 2, 90)


def _stream_offline(fp, kwargs):
    """저장된 답을 조각으로 나눠 스트리밍처럼 돌려준다(키 없이도 스트리밍 실습이 되게)."""
    resp = _replay("chat", fp, kwargs)
    text = resp.choices[0].message.content or ""
    step = 12
    for i in range(0, len(text), step):
        yield _chunk(text[i:i + step])


def _stream_live(fp, kwargs):
    """실제 스트림을 흘려보내면서 전체 답을 모아 캐시에 저장한다."""
    parts = []
    for chunk in _real_client.chat.completions.create(**kwargs):
        piece = chunk.choices[0].delta.content if chunk.choices else None
        if piece:
            parts.append(piece)
        yield chunk
    usage = {"total_tokens": 0, "prompt_tokens": 0, "completion_tokens": 0,
             "completion_tokens_details": {"reasoning_tokens": 0}}
    _remember(fp, {"choices": [{"message": {"content": "".join(parts), "tool_calls": None}}],
                   "usage": usage})


class _ChatCompletions:
    def create(self, **kwargs):
        fp = _fingerprint("chat", kwargs)
        if kwargs.get("stream"):
            # stream 은 캐시 지문에 넣지 않는다 — 같은 질문이면 스트리밍이든 아니든 같은 답을 쓴다
            return _stream_live(fp, kwargs) if _HAS_KEY else _stream_offline(fp, kwargs)
        if _HAS_KEY:
            resp = _call_live(_real_client.chat.completions.create, **kwargs)
            _remember(fp, _dump_chat(resp))
            return resp
        return _replay("chat", fp, kwargs)

    def parse(self, **kwargs):
        """구조화된 출력(pydantic BaseModel) — 결과를 타입이 있는 객체(.parsed)로 돌려준다."""
        fp = _fingerprint("parse", kwargs)
        if _HAS_KEY:
            resp = _call_live(_real_client.chat.completions.parse, **kwargs)
            _remember(fp, _dump_parse(resp))
            return resp
        return _replay_parse(fp, kwargs.get("response_format"))

class _Chat:
    def __init__(self):
        self.completions = _ChatCompletions()

class _Responses:
    def create(self, **kwargs):
        fp = _fingerprint("response", kwargs)
        if _HAS_KEY:
            resp = _call_live(_real_client.responses.create, **kwargs)
            _remember(fp, _dump_response(resp))
            return resp
        return _replay("response", fp, kwargs)

class _OfflineSafeClient:
    def __init__(self):
        self.chat = _Chat()
        self.responses = _Responses()

_real_client = None
if _HAS_KEY:
    from openai import OpenAI
    _real_client = OpenAI(max_retries=6)   # 429(분당 토큰 제한)는 잠시 뒤 자동 재시도

def offline_only():
    """검증 스크립트용 — 키가 있어도 저장된 응답만 쓰게 강제한다(실수로 과금되는 것을 막는다).

    환경변수 DAY14_OFFLINE=1 로도 같은 효과를 낸다.
    """
    global _HAS_KEY
    _HAS_KEY = False


def get_client(quiet: bool = False):
    """실습용 client 를 만든다. 키가 있으면 실제 API, 없으면 저장된 응답.

    한 프로세스에서 노트북을 여러 개 실행하는 경우(검증 스크립트)에도
    노트북마다 재생 위치가 처음부터 시작하도록 _REPLAY_POS 를 비운다.
    """
    global _HAS_KEY
    if os.getenv("DAY14_OFFLINE") == "1":   # 검증 실행 중 실수로 라이브 호출이 나가는 것을 막는 잠금장치
        _HAS_KEY = False
    _REPLAY_POS.clear()
    if not quiet:
        print("OpenAI 클라이언트 준비 완료 —", "실제 API 연결됨" if _HAS_KEY else "오프라인 캐시 응답 모드")
    return _OfflineSafeClient()
