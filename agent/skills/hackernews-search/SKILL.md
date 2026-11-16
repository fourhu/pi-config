---
name: hackernews-search
disable-model-invocation: true
description: Search Hacker News posts and feeds.
---

# Hacker News search

Two modes, no signup:

- **Search** — `read` against the Algolia API, one HTTP GET
- **Feed** — Python script against Firebase for top/new/best

## Search: Algolia via `read`

### URL

`https://hn.algolia.com/api/v1/search?query=<q>&tags=<type>&hitsPerPage=<n>`

### Params

- `query` — required, space-separated
- `tags` — `story` (default) / `comment` / `(story,comment)`
- `hitsPerPage` — 1–30, default 20
- `page` — 0-based

### Examples

```
read "https://hn.algolia.com/api/v1/search?query=deepseek&tags=story&hitsPerPage=15"
read "https://hn.algolia.com/api/v1/search?query=rust+async&tags=comment&hitsPerPage=10"
read "https://hn.algolia.com/api/v1/search?query=linux+kernel&tags=(story,comment)&hitsPerPage=10"
```

Pagination: `&page=<n>`.

### Response

- `hits[]` — `title`, `url`, `objectID` (HN link), `points`, `num_comments`, `author`, `created_at`
- `nbHits` / `nbPages` / `page`

## Feed: Python

Path: `skill://hackernews-search/scripts/hackernews-search.py`. If that path does not resolve, `read` the Firebase endpoints.

```bash
python "<path>" '{"mode":"top","count":10}'
python "<path>" '{"mode":"new","count":10}'
python "<path>" '{"mode":"best","count":10}'
```

- `mode` — `top` / `new` / `best`
- `count` — 1–30, default 10

## Fallback

- Search network error — retry once, then `web_search` `site:news.ycombinator.com <query>`
- Feed script missing — `read` Firebase ID lists, then fetch items in parallel

## Display

```
### HN threads for "<query>"

| # | Title | Points | Comments | Date | Link |
|---|-------|--------|----------|------|------|
| 1 | <title> | <points> | <num_comments> | <date> | [HN](<hn_url>) |

<total> hits.
```
