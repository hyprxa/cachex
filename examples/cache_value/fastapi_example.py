import io

import pandas as pd
from aiohttp import ClientSession
from cacheplus import (
    async_cache_value,
    async_file_storage_factory,
    cache_reference,
)
from fastapi import Depends, FastAPI
from typing import Annotated


DATASETS = {
    50: "https://github.com/plotly/datasets/raw/master/uber-rides-data1.csv",
    5: "https://github.com/plotly/datasets/raw/master/26k-consumer-complaints.csv",
}

app = FastAPI()

@cache_reference()
async def get_client_session() -> ClientSession:
    return ClientSession()


@async_cache_value(
    storage_factory=async_file_storage_factory("./.cache", key_prefix="example"),
    type_encoders={ClientSession: lambda session: id(session)}
)
async def download_data(
    session: Annotated[ClientSession, Depends(get_client_session)],
    size: int
) -> pd.DataFrame:
    url = DATASETS.get(size)
    if url is not None:
        response = await session.get(url)
        buf = io.BytesIO()
        content = await response.read()
        buf.write(content)
        buf.seek(0)
        return pd.read_csv(buf)
    raise ValueError(f"Invalid size: {size}")


@app.get("/data/{size}")
async def get_dataset(data: Annotated[pd.DataFrame, Depends(download_data)]):
    return data.to_json()
