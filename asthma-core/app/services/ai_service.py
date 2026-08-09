"""
AI 大模型调用服务
- 兼容 OpenAI / DeepSeek Chat Completions API
- 支持流式（SSE）和非流式响应
- API Key 由前端通过请求头传入，后端不持久化
"""
import json
from typing import AsyncIterator, Optional

import httpx


# ==================== 默认模型与端点 ====================
DEFAULT_OPENAI_BASE = "https://api.openai.com/v1"
DEFAULT_DEEPSEEK_BASE = "https://api.deepseek.com/v1"

# 推荐模型映射（可被前端传入覆盖）
PROVIDER_DEFAULTS = {
    "openai": {
        "base_url": DEFAULT_OPENAI_BASE,
        "model": "gpt-4o",
    },
    "deepseek": {
        "base_url": DEFAULT_DEEPSEEK_BASE,
        "model": "deepseek-chat",
    },
}


class AIConfigError(Exception):
    """AI 配置异常（Key 缺失/无效/额度耗尽）"""

    def __init__(self, message: str, code: str = "config_error"):
        self.message = message
        self.code = code
        super().__init__(message)


def resolve_provider(provider: str, base_url: str, model: str) -> tuple[str, str]:
    """根据 provider 补全默认 base_url 与 model"""
    if provider not in PROVIDER_DEFAULTS:
        provider = "deepseek"  # 兜底
    defaults = PROVIDER_DEFAULTS[provider]
    if not base_url:
        base_url = defaults["base_url"]
    if not model:
        model = defaults["model"]
    return base_url, model


async def stream_chat(
    messages: list[dict],
    api_key: str,
    provider: str = "deepseek",
    base_url: str = "",
    model: str = "",
    temperature: float = 0.6,
    timeout: float = 120.0,
) -> AsyncIterator[str]:
    """
    流式调用 Chat Completions，逐 chunk 产出增量文本（SSE 格式 data: ...）。

    异常处理：
      - Key 缺失 → AIConfigError(code=key_missing)
      - Key 无效/额度耗尽 → AIConfigError(code=key_invalid/quota_exhausted)
      - 其他网络错误 → 抛出原异常
    """
    if not api_key or not api_key.strip():
        raise AIConfigError("未配置 AI API Key，请在系统设置中填写", code="key_missing")

    base_url, model = resolve_provider(provider, base_url, model)
    url = f"{base_url.rstrip('/')}/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": True,
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            async with client.stream(
                "POST", url, headers=headers, json=payload
            ) as response:
                # 401 / 403 通常是 Key 无效
                if response.status_code == 401:
                    body = await response.aread()
                    raise AIConfigError(
                        "AI API Key 无效或未授权，请检查系统设置",
                        code="key_invalid",
                    )
                if response.status_code == 402 or response.status_code == 429:
                    raise AIConfigError(
                        "AI API 额度已耗尽或触发限流，请充值后重试",
                        code="quota_exhausted",
                    )
                if response.status_code >= 400:
                    body = await response.aread()
                    err_msg = body.decode("utf-8", errors="ignore")[:300]
                    raise AIConfigError(
                        f"AI 服务返回错误 ({response.status_code})：{err_msg}",
                        code="api_error",
                    )

                async for line in response.aiter_lines():
                    if not line:
                        continue
                    # OpenAI SSE 格式：data: {...}
                    if line.startswith("data:"):
                        data = line[5:].strip()
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            delta = (
                                chunk.get("choices", [{}])[0]
                                .get("delta", {})
                                .get("content", "")
                            )
                            if delta:
                                yield delta
                        except (json.JSONDecodeError, IndexError):
                            continue
        except httpx.RequestError as e:
            raise AIConfigError(
                f"AI 服务网络连接失败：{str(e)}", code="network_error"
            ) from e


async def chat_once(
    messages: list[dict],
    api_key: str,
    provider: str = "deepseek",
    base_url: str = "",
    model: str = "",
    temperature: float = 0.6,
    timeout: float = 60.0,
) -> str:
    """非流式调用，返回完整文本"""
    if not api_key or not api_key.strip():
        raise AIConfigError("未配置 AI API Key，请在系统设置中填写", code="key_missing")

    base_url, model = resolve_provider(provider, base_url, model)
    url = f"{base_url.rstrip('/')}/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, headers=headers, json=payload)
        if resp.status_code == 401:
            raise AIConfigError(
                "AI API Key 无效或未授权，请检查系统设置", code="key_invalid"
            )
        if resp.status_code in (402, 429):
            raise AIConfigError(
                "AI API 额度已耗尽或触发限流，请充值后重试",
                code="quota_exhausted",
            )
        if resp.status_code >= 400:
            raise AIConfigError(
                f"AI 服务返回错误 ({resp.status_code})", code="api_error"
            )
        data = resp.json()
        return (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )


# ==================== 报告生成 Prompt ====================

SYSTEM_PROMPT = """# Role: 中医药智能化与网络药理学专家 (TCM & Network Pharmacology Expert)

## Profile
你是一位精通中药复方有效物质基础、药理学、网络药理学及儿童哮喘临床治疗的专家。你的任务是根据系统计算出的"自定义处方入血预测数据及靶点匹配结果"，为用户生成一份结构严谨、逻辑清晰、具备学术深度与临床参考价值的《儿童哮喘中药处方作用机制智能分析报告》。

## Constrains
1. 报告必须严格基于用户传入的结构化 JSON 数据，不得凭空捏造未提供的化合物或靶点关系。
2. 语言表达应当专业、学术、严谨，符合中医药现代化研究规范。
3. 输出格式必须为标准 Markdown 格式，包含层次标题、数据表格、重点加粗和清晰的总结。

## Analysis Workflow
1. **处方组方分析**：根据输入的处方名称与中药组成，从中医理论（君臣佐使、功效）简要分析其平喘止咳、宣肺清热或理气化痰的作用。
2. **血中移行成分（入血成分）评估**：结合预测概率，区分直接入血成分与间接入血/代谢成分，重点阐述 Top 入血化合物的理化性质与潜在暴露量。
3. **网络药理学与靶点机制解析**：分析高结合活性靶点与儿童哮喘疾病靶点（如气道重塑、免疫炎症反应、肥大细胞脱颗粒等）的映射关系。
4. **总结与临床/科研建议**：总结该处方的核心作用机制，并为后续湿实验（如 HPLC-MS 复核、细胞实验）提供建议。
"""


def build_user_prompt(prescription_name: str, herbs_text: str, compounds_md: str, targets_md: str) -> str:
    """拼接 User Prompt"""
    return f"""请根据以下处方的预测与计算数据，生成完整的《儿童哮喘自定义处方智能分析报告》：

### 1. 处方基本信息
- **处方名称**：{prescription_name}
- **组方构成**：{herbs_text}

### 2. 核心入血预测结果 (Top 化合物)
{compounds_md}
*(注：包含化合物名称、来源中药、预测直接/间接入血概率、理化参数 MW/LogP)*

### 3. 核心候选靶点与哮喘通路匹配数据
{targets_md}
*(注：包含定量活性结合数值、相关哮喘病理环节如：IgE介导免疫、气道平滑肌痉挛等)*

---

### 请按以下 Markdown 格式输出报告：

# 《{prescription_name}》治疗儿童哮喘作用机制智能分析报告

## 一、组方配伍与传统功效简析
*(在此结合中医理论分析该处方的配伍特色)*

## 二、处方血中移行成分（入血化合物）精准识别
*(绘制 Markdown 表格列出 Top 入血成分，并对其理化特性与体内暴露潜力进行药理学点评)*

## 三、"成分-靶点-通路" 分子作用机制阐释
*(详细分析核心靶点与儿童哮喘病理环节的关联，解释多成分-多靶点协同作用)*

## 四、科研建议与实验验证方向
*(提出1-2条针对该处方的后续质谱检测或分子生物学验证建议)*
"""
