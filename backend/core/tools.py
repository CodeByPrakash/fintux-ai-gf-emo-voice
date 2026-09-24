import httpx


async def search_wikipedia(query: str) -> str:
    try:
        import wikipedia
        results = wikipedia.search(query, results=3)
        if results:
            page = wikipedia.page(results[0], auto_suggest=False)
            return f"**{page.title}**: {page.summary[:500]}"
        return "No Wikipedia results found."
    except Exception as e:
        return f"Wikipedia error: {e}"


async def search_web(query: str) -> str:
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            if results:
                output = []
                for r in results:
                    output.append(f"- **{r['title']}**: {r['body'][:200]}")
                return "\n".join(output)
        return "No web results found."
    except Exception as e:
        return f"Web search error: {e}"


async def fetch_url(url: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            return resp.text[:2000]
    except Exception as e:
        return f"Fetch error: {e}"


TOOLS = {
    "wiki": search_wikipedia,
    "search": search_web,
    "fetch": fetch_url
}
