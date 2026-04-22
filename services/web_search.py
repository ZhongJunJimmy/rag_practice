from __future__ import annotations

import json
import time
from typing import Any, Dict, List

import requests


from libs.config import CHAT_MODEL, MID_CHAT_MODEL
from libs.ollama_client import client
from services.retrieval import rerank
SEARCH_TIMEOUT = 15


def web_search(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    使用 DuckDuckGo Instant Answer API + HTML fallback 做簡單搜尋。
    不依賴 Ollama 內建 web search。
    """

    results: List[Dict[str, str]] = []

    # 先試 DuckDuckGo Instant Answer API
    try:
        api_url = "https://api.duckduckgo.com/"
        resp = requests.get(
            api_url,
            params={
                "q": query,
                "format": "json",
                "no_redirect": "1",
                "no_html": "1",
                "skip_disambig": "1",
            },
            timeout=SEARCH_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        abstract_text = data.get("AbstractText")
        abstract_url = data.get("AbstractURL")
        heading = data.get("Heading")

        if abstract_text:
            results.append({
                # "title": heading or query,
                # "url": abstract_url or "",
                "text": abstract_text,
            })

        related_topics = data.get("RelatedTopics", [])
        for item in related_topics:
            if isinstance(item, dict):
                if "Text" in item and "FirstURL" in item:
                    results.append({
                        # "title": item.get("Text", "")[:80],
                        # "url": item.get("FirstURL", ""),
                        "text": item.get("Text", ""),
                    })
                elif "Topics" in item:
                    for sub in item["Topics"]:
                        if "Text" in sub and "FirstURL" in sub:
                            results.append({
                                # "title": sub.get("Text", "")[:80],
                                # "url": sub.get("FirstURL", ""),
                                "text": sub.get("Text", ""),
                            })

        if results:
            return {
                "query": query,
                "source": "duckduckgo_instant_answer",
                "results": results[:max_results],
            }

    except Exception as e:
        api_error = str(e)
    else:
        api_error = None

    # fallback：用 DuckDuckGo HTML 搜尋頁做簡單解析
    # 這種方式比較脆弱，但比完全不能用好
    try:
        html_url = "https://html.duckduckgo.com/html/"
        resp = requests.post(
            html_url,
            data={"q": query},
            headers={
                "User-Agent": "Mozilla/5.0",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            timeout=SEARCH_TIMEOUT,
        )
        resp.raise_for_status()
        html = resp.text

        # 非正式 parser，僅做簡單字串切割
        # 實務上可改用 BeautifulSoup
        import re

        pattern = re.compile(
            r'<a[^>]*class="result__a"[^>]*href="(?P<url>.*?)"[^>]*>(?P<title>.*?)</a>.*?'
            r'<a[^>]*class="result__snippet"[^>]*>(?P<snippet>.*?)</a>',
            re.S
        )

        def strip_html(text: str) -> str:
            text = re.sub(r"<.*?>", "", text)
            return (
                text.replace("&amp;", "&")
                .replace("&quot;", '"')
                .replace("&#39;", "'")
                .replace("&lt;", "<")
                .replace("&gt;", ">")
                .strip()
            )

        for m in pattern.finditer(html):
            results.append({
                # "title": strip_html(m.group("title")),
                # "url": strip_html(m.group("url")),
                "text": strip_html(m.group("snippet")),
            })
            if len(results) >= max_results:
                break

        return {
            "query": query,
            # "source": "duckduckgo_html",
            "results": results[:max_results],
        }

    except Exception as e:
        return {
            "query": query,
            "source": "web_search_failed",
            "results": [],
            "error": str(e),
            "api_error": api_error,
        }


def build_tools() -> List[Dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": (
                    "Search the web when the user's question requires current information, "
                    "external facts, recent news, documentation lookup, or verification."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to look up on the internet."
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of search results to return.",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    ]


def call_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    print(f"[Calling tool: {tool_name} with arguments: {arguments}]")
    if tool_name == "web_search":
        query = arguments["query"]
        max_results = arguments.get("max_results", 5)
        return web_search(query=query, max_results=max_results)

    raise ValueError(f"Unknown tool: {tool_name}")


def run_agent(user_question: str) -> str:

    system_prompt = """
You are a tool-using assistant.

When a tool is needed:
- You MUST call the tool using the provided tool calling interface
- You MUST NOT write JSON manually
- You MUST NOT include tool_calls in the message content

Incorrect:
{"tool_calls": [...]}

Correct:
(use the tool_calls field provided by the system)

Do not simulate tool calls in text.

# Tool usage policy (IMPORTANT)
- You MUST use tools if the question requires:
  - up-to-date information (news, prices, weather, current events)
  - factual data you are not highly confident about
  - external or real-world knowledge not guaranteed to be in your training data
- If there is any uncertainty, prefer using a tool instead of guessing
- DO NOT answer from memory when accuracy is important

# Response policy (IMPORTANT)
- If no tool is used, keep the answer concise and to the point
- Avoid unnecessary explanations, examples, or repetition
- Prefer short, direct answers unless the user explicitly asks for details
- Limit the answer to 2-3 sentences if possible, unless the question is complex

# Language
- Match the user's language
""".strip()

    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_question},
    ]

    tools = build_tools()

    # 第一次讓模型判斷是否要呼叫工具
    response = client.chat(
        model=CHAT_MODEL,
        messages=messages,
        tools=tools,
    )

    message = response["message"]
    messages.append(message)
    tool_calls = message.get("tool_calls", [])

    # 如果模型決定要呼叫工具，就執行
    if tool_calls:
        for tool_call in tool_calls:
            func = tool_call["function"]
            tool_name = func["name"]
            arguments = func.get("arguments", {})

            tool_result = call_tool(tool_name, arguments)
            reranked = rerank(user_question, tool_result["results"], top_k=3)
            messages.append(
                {
                    "role": "tool",
                    "name": tool_name,
                    "content": json.dumps(reranked, ensure_ascii=False),
                }
            )

        # 再呼叫一次模型，讓它根據 tool 結果回答
        final_response = client.chat(
            model=CHAT_MODEL,
            messages=messages,
        )
        return final_response["message"]["content"]

    # 如果不需要工具，直接回傳第一次答案
    return message["content"]
