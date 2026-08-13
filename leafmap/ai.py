"""leafmap.ai - Natural Language Mapping (自然语言制图)

Turn plain-language descriptions into ready-to-run leafmap mapping code.

Features
--------
- 自然语言描述 -> leafmap 代码：输入"画南京市河流图"这类中文描述，
  自动生成并执行 leafmap 制图代码，输出交互式 HTML 地图。
- 多 LLM 后端：OpenAI / DeepSeek / Ollama 等 OpenAI 兼容接口，
  通过环境变量或参数指定，默认读取 LEAFMAP_LLM_* 环境变量。
- 安全沙箱：生成代码先做 AST 静态校验（模块/函数/属性白名单），
  再在受限命名空间中执行，避免恶意代码调用系统命令或读写敏感文件。
- 与 leafmap 原生 CLI 无缝集成：``leafmap ai-map "描述"``。

Usage
-----
::

    import leafmap.ai as ai

    # 一次性调用（指定输出路径）
    ai.natural_map("南京市河流分布图", output="nanjing_rivers.html")

    # 只生成代码不执行（方便自己改）
    code = ai.generate_code("全球地震点分布")

    # 从环境变量读取 API 配置
    # LEAFMAP_LLM_BASE_URL=https://api.deepseek.com/v1
    # LEAFMAP_LLM_API_KEY=sk-xxx
    # LEAFMAP_LLM_MODEL=deepseek-chat
"""

import ast
import os
import re
import tempfile
import time
import traceback
import urllib.request
import urllib.error
import json
from pathlib import Path

__all__ = [
    "generate_code",
    "natural_map",
    "ai_map",
    "run_safe_code",
    "repair_code",
    "REPAIR_SYSTEM_PROMPT",
    "LLMConfig",
    "demo",
]

DEFAULT_SYSTEM_PROMPT = """你是一个专业的地理空间制图专家。用户会用自然语言描述一张地图，你需要生成完整的 Python 代码来绘制这张地图。

规则：
1. 只能使用以下白名单模块：leafmap, folium, geopandas, pandas, numpy, matplotlib
2. 必须使用 leafmap 的 folium 后端（leafmap.Map(backend="folium") 或直接 leafmap.Map() 并确保能用 folium 渲染）
3. 代码结构必须是：
   import leafmap
   # 可选：import geopandas as gpd, pandas as pd, numpy as np, matplotlib...

   m = leafmap.Map(center=[纬度, 经度], zoom=缩放级别)
   # ... 添加图层、数据、标注 ...

   # 最后一行导出 HTML（OUTPUT_PATH 变量会自动替换为输出路径）
   m.to_html(OUTPUT_PATH)

4. 必须通过变量 OUTPUT_PATH 保存地图，不要硬编码其他输出路径
5. 如果用户描述中需要真实地理数据（如河流、行政边界等），优先尝试使用内置数据或示例数据：
   - leafmap 自带示例数据可通过 leafmap.sample_data 或 folium 内置 GeoJSON 获取
   - 如果无法获取真实数据，可以使用合理的模拟数据（标注为模拟数据）
6. 只输出 Python 代码，不要输出解释、不要使用 markdown 代码块标记
7. 中心点坐标要合理（中国地图中心约 [35, 105]，南京约 [32.06, 118.80]，北京约 [39.90, 116.40]）
8. 图层、颜色、标注等要让地图美观且信息明确
"""


class LLMConfig:
    """LLM 调用配置。

    支持 OpenAI 兼容接口。优先使用参数传入的值，否则读环境变量：
    - LEAFMAP_LLM_BASE_URL：API 地址（默认 https://api.deepseek.com/v1）
    - LEAFMAP_LLM_API_KEY：API Key
    - LEAFMAP_LLM_MODEL：模型名（默认 deepseek-chat）
    """

    def __init__(
        self,
        base_url=None,
        api_key=None,
        model=None,
        temperature=0.2,
        max_tokens=4096,
        timeout=120,
    ):
        self.base_url = (
            base_url
            or os.environ.get("LEAFMAP_LLM_BASE_URL")
            or "https://api.deepseek.com/v1"
        )
        self.api_key = api_key or os.environ.get("LEAFMAP_LLM_API_KEY") or ""
        self.model = model or os.environ.get("LEAFMAP_LLM_MODEL") or "deepseek-chat"
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

    def __repr__(self):
        return f"LLMConfig(base_url={self.base_url!r}, model={self.model!r}, api_key={'***' if self.api_key else '(empty)'})"


# ---------------------------------------------------------------------------
# 安全沙箱：AST 白名单校验
# ---------------------------------------------------------------------------

# 允许导入的顶级模块
ALLOWED_IMPORTS = {
    "leafmap",
    "folium",
    "geopandas",
    "pandas",
    "numpy",
    "matplotlib",
    "matplotlib.pyplot",
    "json",
    "math",
    "random",
    "datetime",
    "osmnx",  # 保留：网络分析
}

# 禁止调用的危险属性/方法（粗粒度黑名单）
FORBIDDEN_ATTRS = {
    "system",
    "popen",
    "spawn",
    "exec",
    "eval",
    "compile",
    "open",
    "remove",
    "unlink",
    "rmdir",
    "mkdir",
    "chmod",
    "chown",
    "rename",
    "replace",
    "globals",
    "locals",
    "vars",
    "getattr",
    "setattr",
    "delattr",
    "__import__",
    "__subclasses__",
    "__globals__",
    "__builtins__",
    "__class__",
    "__mro__",
    "__bases__",
    "subprocess",
    "socket",
    "requests",
    "urllib",
    "http",
    "shutil",
    "pathlib",
    "os",
    "sys",
}

FORBIDDEN_MODULES = {
    "os",
    "sys",
    "subprocess",
    "socket",
    "shutil",
    "pathlib",
    "requests",
    "urllib",
    "http",
    "importlib",
    "ctypes",
    "pickle",
    "shelve",
}


class SafetyError(Exception):
    """安全校验未通过。"""


def _check_ast_safety(code: str) -> None:
    """AST 静态校验：检查 import / 危险属性 / 危险调用。"""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise SafetyError(f"生成的代码语法错误: {e}")

    for node in ast.walk(tree):
        # import 语句校验
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root not in ALLOWED_IMPORTS and alias.name not in ALLOWED_IMPORTS:
                    raise SafetyError(f"禁止导入模块: {alias.name}")
        if isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if node.module not in ALLOWED_IMPORTS and root not in ALLOWED_IMPORTS:
                raise SafetyError(f"禁止导入模块: {node.module}")

        # 属性访问黑名单
        if isinstance(node, ast.Attribute):
            attr = node.attr
            if attr in FORBIDDEN_ATTRS:
                raise SafetyError(f"禁止访问属性/方法: {attr}")

        # 调用黑名单（Name 直接调用，如 open(...)）
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in FORBIDDEN_ATTRS:
                raise SafetyError(f"禁止调用: {node.func.id}()")

        # 字符串中含危险路径模式（粗略检查）
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            low = node.value.lower()
            if re.search(r"(?<!_)__(import|globals|builtins|class|subclasses)", low):
                raise SafetyError(f"检测到危险魔法属性引用: {node.value!r}")


def _safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    """受限 __import__：仅允许白名单模块导入（运行时兜底，防动态导入绕过）。"""
    root = name.split(".")[0]
    if root not in ALLOWED_IMPORTS and name not in ALLOWED_IMPORTS:
        raise SafetyError(f"禁止导入模块: {name}")
    return __import__(name, globals, locals, fromlist, level)


def _sanitize_code(code: str) -> str:
    """清理 LLM 输出：去掉 markdown 代码块标记等。"""
    code = code.strip()
    # 去掉 ```python ... ``` 包裹
    fence = re.search(r"```(?:python|py)?\s*\n(.*?)```", code, re.S)
    if fence:
        code = fence.group(1).strip()
    # 去掉可能的前缀文本（如 "好的，以下是代码："）
    first_line = code.splitlines()[0] if code.splitlines() else ""
    if not first_line.lstrip().startswith(("import", "from", "#", "m =", "m=")):
        lines = code.splitlines()
        for i, line in enumerate(lines):
            if line.lstrip().startswith(("import", "from", "m =", "m=", "#")):
                code = "\n".join(lines[i:])
                break
    return code.strip()


# ---------------------------------------------------------------------------
# LLM 调用
# ---------------------------------------------------------------------------


def _chat_once(messages, config: LLMConfig):
    """调用 OpenAI 兼容接口，返回回复文本。"""
    if not config.api_key:
        raise ValueError(
            "未配置 LLM API Key。请设置环境变量 LEAFMAP_LLM_API_KEY，"
            "或调用时传入 api_key 参数，例如 natural_map(..., api_key='sk-xxx')。"
        )
    url = config.base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": config.model,
        "messages": messages,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
        "stream": False,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=config.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"LLM 接口返回 HTTP {e.code}: {body[:500]}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"无法连接 LLM 接口 {url}: {e.reason}")

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise RuntimeError(f"LLM 接口返回格式异常: {str(data)[:500]}")


def _chat_with_retry(messages, config: LLMConfig, retries: int = 2):
    """带重试的 LLM 调用（网络抖动时自动重试）。"""
    last_err = None
    for attempt in range(retries + 1):
        try:
            return _chat_once(messages, config)
        except RuntimeError as e:
            last_err = e
            if attempt < retries:
                time.sleep(2 * (attempt + 1))
    raise last_err


# ---------------------------------------------------------------------------
# 成功案例缓存
# ---------------------------------------------------------------------------

import hashlib

CACHE_FILENAME = "leafmap_ai_cache.json"


def _cache_path(custom_path=None):
    """返回缓存文件路径：默认 ~/.leafmap/leafmap_ai_cache.json。"""
    if custom_path:
        return str(custom_path)
    home = Path.home() / ".leafmap"
    home.mkdir(parents=True, exist_ok=True)
    return str(home / CACHE_FILENAME)


def _cache_load(cache_path=None):
    """读取缓存 JSON；不存在或损坏时返回空字典。"""
    p = Path(_cache_path(cache_path))
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _cache_save(cache, cache_path=None):
    """写回缓存 JSON（失败静默，不阻塞主流程）。"""
    p = Path(_cache_path(cache_path))
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def _cache_key(description: str) -> str:
    """根据描述生成缓存键（前 16 位 sha256，足够区分）。"""
    return hashlib.sha256(description.strip().encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------------------
# 代码修复（Repair Loop）
# ---------------------------------------------------------------------------

REPAIR_SYSTEM_PROMPT = """你是地理空间制图代码修复专家。用户之前生成的一段 leafmap 制图代码在执行时失败了，你需要根据错误信息修复这段代码。

规则：
1. 分析错误信息和 traceback，找出失败原因（API 用法错误、参数错误、数据缺失、语法错误等）
2. 输出修复后的完整 Python 代码，保持原有意图不变
3. 只能使用白名单模块：leafmap, folium, geopandas, pandas, numpy, matplotlib
4. 必须通过变量 OUTPUT_PATH 保存地图
5. 只输出 Python 代码，不要输出解释、不要使用 markdown 代码块标记
6. 如果错误无法通过修改代码解决（如外部数据源不可达），请使用合理的模拟数据或内置数据替代，并在代码注释中说明
7. 不要为了规避错误而调用危险函数（open、os、subprocess 等），遵守与原始生成相同的安全约束
"""


def repair_code(
    code: str,
    error: str,
    traceback_text: str,
    description: str = "",
    config: LLMConfig = None,
    system_prompt: str = None,
    history: list = None,
) -> str:
    """将失败代码 + 错误信息回喂给 LLM，返回修复后的代码。

    Parameters
    ----------
    code : str
        执行失败的原始代码。
    error : str
        错误信息（result["error"]）。
    traceback_text : str
        完整 traceback（result["traceback"]）。
    description : str, optional
        原始地图描述，帮助 LLM 保持意图。
    config : LLMConfig, optional
        LLM 配置。
    system_prompt : str, optional
        自定义修复提示词。
    history : list, optional
        历史修复记录列表，每项为 dict：
        {"attempt": int, "error": str, "traceback": str}。
        携带历史错误可避免 LLM 重复犯同样的错。

    Returns
    -------
    str
        修复后的代码。
    """
    config = config or LLMConfig()
    sys_prompt = system_prompt or REPAIR_SYSTEM_PROMPT
    user_prompt = (
        f"原始地图描述：{description}\n\n"
        f"--- 失败的代码 ---\n```python\n{code}\n```\n\n"
        f"--- 错误信息 ---\n{error}\n\n"
        f"--- Traceback ---\n```\n{traceback_text}\n```\n"
    )
    if history:
        user_prompt += "\n--- 之前的失败尝试（请避免重复同样的错误）---\n"
        for h in history:
            user_prompt += (
                f"\n[第 {h.get('attempt', '?')} 次尝试]\n"
                f"错误: {h.get('error', '')}\n"
                f"Traceback:\n```\n{h.get('traceback', '')}\n```\n"
            )
    user_prompt += "\n请输出修复后的完整 Python 代码。"
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_prompt},
    ]
    fixed = _chat_with_retry(messages, config)
    return _sanitize_code(fixed)


# ---------------------------------------------------------------------------
# 代码生成
# ---------------------------------------------------------------------------


def generate_code(
    description: str,
    config: LLMConfig = None,
    system_prompt: str = None,
    extra_context: str = "",
) -> str:
    """根据自然语言描述生成 leafmap 制图代码。

    Parameters
    ----------
    description : str
        地图描述，如 "南京市河流分布图"、"全球地震点分布"。
    config : LLMConfig, optional
        LLM 配置；None 时读取环境变量。
    system_prompt : str, optional
        自定义系统提示词；None 时使用内置默认。
    extra_context : str, optional
        额外的上下文提示（如数据文件路径、约束条件）。

    Returns
    -------
    str
        生成的 Python 代码。
    """
    config = config or LLMConfig()
    sys_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
    user_prompt = f"用户想绘制的地图：{description}\n"
    if extra_context:
        user_prompt += f"额外上下文：{extra_context}\n"
    user_prompt += "请直接输出完整的 Python 代码。"
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_prompt},
    ]
    code = _chat_with_retry(messages, config)
    return _sanitize_code(code)


# ---------------------------------------------------------------------------
# 安全执行
# ---------------------------------------------------------------------------


def run_safe_code(
    code: str,
    output_path: str = None,
    safe_globals: dict = None,
) -> dict:
    """在受限命名空间中安全执行生成的代码。

    Parameters
    ----------
    code : str
        要执行的代码。
    output_path : str, optional
        OUTPUT_PATH 变量值（代码中最后一行的导出目标）。
    safe_globals : dict, optional
        额外的全局变量注入。

    Returns
    -------
    dict
        包含执行结果：{"ok": bool, "error": str|None, "output_path": str|None}
    """
    _check_ast_safety(code)

    # 注入 OUTPUT_PATH 与必要模块
    out_path = os.path.abspath(output_path) if output_path else None
    if out_path:
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    g = {
        "OUTPUT_PATH": out_path,
        "__name__": "__leafmap_ai__",
        "__builtins__": {
            "__import__": _safe_import,
            "print": print,
            "len": len,
            "range": range,
            "int": int,
            "float": float,
            "str": str,
            "list": list,
            "dict": dict,
            "tuple": tuple,
            "set": set,
            "bool": bool,
            "True": True,
            "False": False,
            "None": None,
            "abs": abs,
            "min": min,
            "max": max,
            "sum": sum,
            "round": round,
            "enumerate": enumerate,
            "zip": zip,
            "isinstance": isinstance,
            "type": type,
            "Exception": Exception,
            "ValueError": ValueError,
            "KeyError": KeyError,
            "IndexError": IndexError,
            "TypeError": TypeError,
            "RuntimeError": RuntimeError,
        },
    }
    if safe_globals:
        g.update(safe_globals)

    try:
        exec(compile(code, "<leafmap-ai>", "exec"), g)
        return {"ok": True, "error": None, "output_path": out_path}
    except Exception as e:
        tb = traceback.format_exc()
        return {"ok": False, "error": str(e), "traceback": tb, "output_path": out_path}


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------


def natural_map(
    description: str,
    output: str = None,
    api_key: str = None,
    base_url: str = None,
    model: str = None,
    execute: bool = True,
    config: LLMConfig = None,
    system_prompt: str = None,
    extra_context: str = "",
    verbose: bool = True,
    max_repairs: int = 2,
):
    """自然语言制图：描述 -> 代码 -> 交互式 HTML 地图（带失败自修复循环）。

    Parameters
    ----------
    description : str
        地图描述（中文/英文均可）。
    output : str, optional
        输出 HTML 路径；None 时使用临时文件，并在完成后打印路径。
    api_key / base_url / model : str, optional
        覆盖 LLM 配置。
    execute : bool, default True
        是否执行生成的代码；False 只生成代码不执行。
    config : LLMConfig, optional
        完整 LLM 配置（优先级最高）。
    system_prompt : str, optional
        自定义系统提示词。
    extra_context : str, optional
        额外上下文。
    verbose : bool, default True
        是否打印过程信息。
    max_repairs : int, default 2
        执行失败后的最大自修复轮数（0 表示关闭自修复，与旧版行为一致）。

    Returns
    -------
    tuple
        (code, result) 其中 result 为 run_safe_code 返回的 dict；
        execute=False 时 result 为 None。
    """
    if config is None:
        config = LLMConfig(base_url=base_url, api_key=api_key, model=model)

    if verbose:
        print(f"[leafmap.ai] 配置: {config}")
        print(f"[leafmap.ai] 描述: {description}")

    # 成功案例缓存：相同描述命中时直接复用，跳过 LLM 调用
    cache = _cache_load()
    cached = cache.get(_cache_key(description)) if cache else None
    if cached and cached.get("code"):
        if verbose:
            print("[leafmap.ai] 命中成功案例缓存，直接复用代码")
        code = cached["code"]
    else:
        code = generate_code(
            description,
            config=config,
            system_prompt=system_prompt,
            extra_context=extra_context,
        )

    if verbose:
        print("[leafmap.ai] 生成的代码:")
        print("-" * 60)
        print(code)
        print("-" * 60)

    if not execute:
        return code, None

    if output is None:
        fd, output = tempfile.mkstemp(suffix=".html", prefix="leafmap_ai_")
        os.close(fd)

    result = run_safe_code(code, output_path=output)
    attempt = 0
    history = []  # 错误历史记忆：累积每次修复的 error/traceback，帮助 LLM 避免重复犯错

    # 失败自修复循环：把报错回喂 LLM，修复后重跑
    while (not result["ok"]) and (attempt < max_repairs):
        attempt += 1
        if verbose:
            print(
                f"[leafmap.ai] 第 {attempt}/{max_repairs} 次修复: {result.get('error')}"
            )
        try:
            code = repair_code(
                code,
                error=result.get("error", ""),
                traceback_text=result.get("traceback", ""),
                description=description,
                config=config,
                system_prompt=system_prompt,
                history=history,
            )
        except Exception as e:
            if verbose:
                print(f"[leafmap.ai] 修复调用失败: {e}")
            break
        if verbose:
            print(f"[leafmap.ai] 修复后的代码:")
            print("-" * 60)
            print(code)
            print("-" * 60)
        result = run_safe_code(code, output_path=output)
        # 记录本次错误，供后续修复参考
        history.append(
            {
                "attempt": attempt,
                "error": result.get("error", ""),
                "traceback": result.get("traceback", ""),
            }
        )

    if result["ok"]:
        # 成功案例缓存：保存本次成功的代码，下次相同描述直接复用
        _cache_save(_cache_key(description), code)
        if verbose:
            print(f"[leafmap.ai] 成功！地图已保存: {output}")
            if attempt > 0:
                print(f"[leafmap.ai] 经过 {attempt} 次自动修复后成功")
    else:
        if verbose:
            print(f"[leafmap.ai] 执行失败: {result.get('error')}")
            if result.get("traceback"):
                print(result["traceback"])
    return code, result


# 别名（与 leafmap 风格保持一致）
ai_map = natural_map


def main():
    """CLI 入口测试。"""
    import argparse

    parser = argparse.ArgumentParser(description="leafmap.ai - 自然语言制图")
    parser.add_argument("description", help="地图描述，如：南京市河流分布图")
    parser.add_argument("-o", "--output", help="输出 HTML 路径")
    parser.add_argument("--no-execute", action="store_true", help="只生成代码不执行")
    args = parser.parse_args()

    natural_map(
        args.description,
        output=args.output,
        execute=not args.no_execute,
    )


def demo():
    """启动 Gradio Web Demo：在浏览器中通过自然语言生成地图。

    运行方式:
        python -m leafmap.ai.demo 或 leafmap ai-demo
    """
    try:
        import gradio as gr
    except ImportError as e:
        raise ImportError("Gradio 未安装，请先执行: pip install gradio") from e

    def _generate(description: str, max_repairs: int, show_code: bool):
        if not description.strip():
            return "请输入地图描述", None
        code, result = natural_map(
            description,
            output=None,
            execute=True,
            max_repairs=max_repairs,
            verbose=False,
        )
        if result["ok"]:
            html_path = result.get("output") or code
            return f"✅ 生成成功: {html_path}", (html_path if show_code else None)
        return f"❌ 执行失败: {result.get('error')}", code if show_code else None

    with gr.Blocks(title="leafmap.ai - 自然语言制图") as app:
        gr.Markdown(
            "# leafmap.ai\n\n"
            "输入地图描述（如 `南京市河流分布图`），自动生成交互式地图 HTML。"
        )
        with gr.Row():
            description = gr.Textbox(
                label="地图描述",
                placeholder="例如：南京市河流分布图 / 中国省会城市点图",
                lines=2,
            )
        with gr.Row():
            max_repairs = gr.Slider(
                minimum=0, maximum=5, value=2, step=1, label="最大自修复次数"
            )
            show_code = gr.Checkbox(label="同时显示生成的代码", value=False)
        with gr.Row():
            btn = gr.Button("生成地图", variant="primary")
        output = gr.Markdown(label="结果")
        code_box = gr.Code(label="生成的代码", language="python")

        btn.click(
            _generate,
            inputs=[description, max_repairs, show_code],
            outputs=[output, code_box],
        )

    app.launch()


if __name__ == "__main__":
    main()
