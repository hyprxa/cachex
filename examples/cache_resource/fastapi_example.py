from aiohttp import ClientSession
from cacheplus import cache_reference
from fastapi import Depends, FastAPI
from typing import Annotated


JSON_PLACEHOLDER = "https://jsonplaceholder.typicode.com/"
DUMMY_JSON = "https://dummyjson.com/"
REPOS = {
    "placeholder": JSON_PLACEHOLDER,
    "dummy": DUMMY_JSON,
}

app = FastAPI()

@cache_reference()
async def get_client_session(repo: str) -> ClientSession:
    base_url = REPOS.get(repo.lower())
    if base_url is not None:
        return ClientSession(base_url)
    raise ValueError(f"Invalid repo: {repo}")

@app.get("/comments/{num}")
async def get_comments(
	session: Annotated[ClientSession, Depends(get_client_session)],
    num: int
):
    response = await session.get(f"/comments/{num}")
    return await response.json()