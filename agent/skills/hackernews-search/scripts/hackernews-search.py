#!/usr/bin/env python3
"""Hacker News search skill script (Python stdlib only).

Modes:
- search (Algolia): query stories/comments
- feed (Firebase): top/new/best lists
"""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Any, Dict, List, NoReturn
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SEARCH_BASE = "https://hn.algolia.com/api/v1"
FIREBASE_BASE = "https://hacker-news.firebaseio.com/v0"
REQUEST_TIMEOUT_SECONDS = 10
EXCERPT_MAX_LENGTH = 300
MAX_FEED_ITEMS = 30
MAX_SEARCH_ITEMS = 30


def print_usage() -> None:
    print(
        "Usage:\n"
        "  # Search mode\n"
        "  python hackernews-search.py '{\"query\":\"rust async\",\"count\":5}'\n"
        "  python hackernews-search.py '{\"query\":\"python\",\"count\":5,\"type\":\"comment\"}'\n"
        "  # Feed mode\n"
        "  python hackernews-search.py '{\"mode\":\"top\",\"count\":10}'\n"
        "  python hackernews-search.py '{\"mode\":\"new\",\"count\":10}'\n"
        "  python hackernews-search.py '{\"mode\":\"best\",\"count\":10}'\n\n"
        "No auth or API key required.\n"
    )


def die(message: str, *, body: Any = None) -> NoReturn:
    payload: Dict[str, Any] = {"error": message, "exit_code": 1}
    if body is not None:
        payload["body"] = str(body)
    print(json.dumps(payload, ensure_ascii=False))
    raise SystemExit(1)


def parse_payload(raw: str) -> Dict[str, Any]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        die(f"Invalid JSON payload: {exc}")
    if not isinstance(data, dict):
        die("Payload must be a JSON object")
    return data


def parse_count(payload: Dict[str, Any], max_val: int) -> int:
    raw = payload.get("count", payload.get("Count", 10))
    try:
        count = int(raw)
    except (TypeError, ValueError):
        return 10
    return max(1, min(max_val, count))


def _http_get(url: str) -> Dict[str, Any]:
    """GET and parse JSON."""
    req = Request(url, headers={"User-Agent": "hackernews-search-skill/1.0"})
    try:
        with urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        die(f"HTTP {exc.code}: {exc.reason}")
    except URLError as exc:
        die(f"HTTP request failed (network error): {exc.reason}")
    except json.JSONDecodeError:
        die("Non-JSON response from API")


# ─── Search mode (Algolia) ────────────────────────────────────────────

VALID_SEARCH_TYPES = {"story", "comment", "all"}


def _parse_search_type(payload: Dict[str, Any]) -> str:
    t = payload.get("type") or payload.get("Type") or "story"
    t = str(t).strip().lower()
    if t not in VALID_SEARCH_TYPES:
        die(f"Invalid type '{t}', must be one of {sorted(VALID_SEARCH_TYPES)}")
    return t


def _build_algolia_tags(search_type: str) -> str:
    if search_type == "story":
        return "story"
    elif search_type == "comment":
        return "comment"
    else:
        return "(story,comment)"


def _build_search_item(hit: Dict[str, Any], search_type: str) -> Dict[str, Any]:
    is_story = search_type in ("story", "all") and bool(hit.get("title"))
    item: Dict[str, Any] = {
        "url": hit.get("url"),
        "hn_url": f"https://news.ycombinator.com/item?id={hit['objectID']}",
    }

    if is_story:
        item["title"] = hit.get("title", "")
        item["type"] = "story"
        item["points"] = hit.get("points", 0)
        item["num_comments"] = hit.get("num_comments", 0)
        # story_text is the Show HN / Ask HN body
        story_text = hit.get("story_text")
        if story_text:
            item["excerpt"] = _truncate(_strip_html(story_text))
    else:
        item["type"] = "comment"
        # comments use the parent story title
        story_title = hit.get("story_title") or ""
        item["title"] = f"[comment] {story_title}" if story_title else "[comment]"
        item["story_title"] = story_title
        item["story_url"] = hit.get("story_url")
        comment_text = hit.get("comment_text") or ""
        if comment_text:
            item["excerpt"] = _truncate(_strip_html(comment_text))

    item["author"] = hit.get("author", "")
    item["created_at"] = hit.get("created_at", "")
    return item


def search_hn(query: str, count: int, search_type: str) -> Dict[str, Any]:
    tags = _build_algolia_tags(search_type)
    params = {
        "query": query,
        "tags": tags,
        "hitsPerPage": str(count),
    }
    url = f"{SEARCH_BASE}/search?{urlencode(params)}"
    data = _http_get(url)

    items = [_build_search_item(hit, search_type) for hit in data.get("hits", [])]
    return {
        "item_count": len(items),
        "items": items,
        "total_hits": data.get("nbHits", 0),
        "page": data.get("page", 0),
    }


# ─── Feed mode (Firebase) ────────────────────────────────────────────

VALID_FEEDS = {"top", "new", "best"}


def _parse_feed_mode(payload: Dict[str, Any]) -> str:
    mode = payload.get("mode") or payload.get("Mode") or ""
    mode = str(mode).strip().lower()
    if mode not in VALID_FEEDS:
        die(f"Invalid mode '{mode}', must be one of {sorted(VALID_FEEDS)}")
    return mode


def _fetch_item(item_id: int) -> Dict[str, Any]:
    url = f"{FIREBASE_BASE}/item/{item_id}.json"
    return _http_get(url)


def _build_feed_item(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "title": item.get("title", ""),
        "url": item.get("url"),
        "hn_url": f"https://news.ycombinator.com/item?id={item['id']}",
        "points": item.get("score", 0),
        "num_comments": item.get("descendants", 0),
        "author": item.get("by", ""),
        "type": item.get("type", "story"),
    }


def feed_hn(mode: str, count: int) -> Dict[str, Any]:
    # 1) id list
    url = f"{FIREBASE_BASE}/{mode}stories.json"
    ids = _http_get(url)

    if not isinstance(ids, list):
        die(f"Unexpected response from Firebase: expected list, got {type(ids).__name__}")

    # 2) fetch items
    items: List[Dict[str, Any]] = []
    for item_id in ids[:count]:
        item = _fetch_item(item_id)
        # stories only; skip job/poll
        if item and item.get("type") == "story":
            items.append(_build_feed_item(item))

    return {
        "item_count": len(items),
        "items": items,
        "feed": mode,
    }


# ─── Helpers ──────────────────────────────────────────────────────────

def _strip_html(text: str) -> str:
    """Strip tags and unescape entities."""
    import html as _html
    import re
    text = re.sub(r"<[^>]+>", " ", text)
    text = _html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _truncate(text: str) -> str:
    if len(text) <= EXCERPT_MAX_LENGTH:
        return text
    return text[:EXCERPT_MAX_LENGTH] + "…"


# ─── Main ─────────────────────────────────────────────────────────────

def main() -> None:
    if len(sys.argv) >= 2 and sys.argv[1] in {"-h", "--help"}:
        print_usage()
        raise SystemExit(0)

    if len(sys.argv) < 2:
        print_usage()
        die("Missing JSON payload argument")

    payload = parse_payload(sys.argv[1])

    # pick mode
    mode = (payload.get("mode") or payload.get("Mode") or "").strip().lower()
    query = (payload.get("query") or payload.get("Query") or "").strip()

    if mode:
        # feed
        feed_mode = _parse_feed_mode(payload)
        count = parse_count(payload, MAX_FEED_ITEMS)
        result = feed_hn(feed_mode, count)
    elif query:
        # search
        count = parse_count(payload, MAX_SEARCH_ITEMS)
        search_type = _parse_search_type(payload)
        result = search_hn(query, count, search_type)
    else:
        die("query or mode is required")

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
