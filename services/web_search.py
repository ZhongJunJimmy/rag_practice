from __future__ import annotations

import json
import time
import html
from typing import Any, Dict, List
from concurrent.futures import ThreadPoolExecutor

import requests

from libs.config import CHAT_MODEL, MID_CHAT_MODEL
from libs.ollama_client import client
from libs.prompts import AGENT_SYSTEM_PROMPT
from services.retrieval import rerank

SEARCH_TIMEOUT = 15
debug_mode = True

def web_search(query: str, max_results: int = 10) -> Dict[str, Any]:
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

        if abstract_text:
            results.append({
                "text": abstract_text,
            })

        related_topics = data.get("RelatedTopics", [])
        for item in related_topics:
            if isinstance(item, dict):
                if "Text" in item and "FirstURL" in item:
                    results.append({
                        "text": item.get("Text", ""),
                    })
                elif "Topics" in item:
                    for sub in item["Topics"]:
                        if "Text" in sub and "FirstURL" in sub:
                            results.append({
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
        html_content = resp.text

        import re

        pattern = re.compile(
            r'<a[^>]*class="result__a"[^>]*href="(?P<url>.*?)"[^>]*>(?P<title>.*?)</a>.*?'
            r'<a[^>]*class="result__snippet"[^>]*>(?P<snippet>.*?)</a>',
            re.S
        )

        def strip_html(text: str) -> str:
            # Remove HTML tags
            text = re.sub(r"<.*?>", "", text)
            # Use standard library to unescape HTML entities (& etc.)
            return html.unescape(text).strip()

        for m in pattern.finditer(html_content):
            results.append({
                "text": strip_html(m.group("snippet")),
            })
            if len(results) >= max_results:
                break

        return {
            "query": query,
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
                            "default": 10
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

def trim_context(messages: List[Dict[str, Any]], max_tool_content_len: int = 4000) -> List[Dict[str, Any]]:
    """
    Simple context management: trim tool results if they are too long to prevent token overflow.
    """
    for msg in messages:
        if msg["role"] == "tool" and len(msg["content"]) > max_tool_content_len:
            msg["content"] = msg["content"][:max_tool_content_len] + "... [truncated]"
    return messages

def run_agent(user_question: str) -> str:
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": user_question},
    ]

    tools = build_tools()
    iterations = 0
    max_iterations = 3

    while iterations < max_iterations:
        response = client.chat(
            model=CHAT_MODEL,
            messages=messages,
            tools=tools,
        )

        message = response["message"]
        messages.append(message)
        tool_calls = message.get("tool_calls", [])

        if not tool_calls:
            return message["content"]

        # Parallel Tool Execution
        def execute_tool_call(tool_call):
            func = tool_call["function"]
            tool_name = func["name"]
            arguments = func.get("arguments", {})
            try:
                result = call_tool(tool_name, arguments)
                # Apply reranking for web_search
                if tool_name == "web_search" and "results" in result:
                    reranked = rerank(user_question, result["results"], top_k=5)
                    return tool_name, reranked
                return tool_name, result
            except Exception as e:
                return tool_name, {"error": str(e)}

        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(execute_tool_call, tc) for tc in tool_calls]
            results = [f.result() for f in futures]

        for tool_name, content in results:
            if debug_mode:
                print(f"[Tool result for {tool_name}: {json.dumps(content, ensure_ascii=False)}]")
            
            messages.append(
                {
                    "role": "tool",
                    "name": tool_name,
                    "content": json.dumps(content, ensure_ascii=False),
                }
            )
        
        # Context Management
        messages = trim_context(messages)
        
        iterations += 1
        if debug_mode:
            print(f"[Iteration {iterations}/{max_iterations} complete]")

    # Final response force summary
    final_response = client.chat(
        model=CHAT_MODEL,
        messages=messages + [{"role": "system", "content": "Please provide the final answer based on the information gathered. Do not call more tools."}],
    )
    return final_response["message"]["content"]