import requests
from bs4 import BeautifulSoup
from gnews import GNews
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryParams(BaseModel):
    max_results: int = 50
    country: str = None
    language: str = None
    start_date: tuple[int, int, int] = None
    end_date: tuple[int, int, int] = None


@app.get("/search_results/")
def get_news(
    query: str | None = None,
    max_results: int = 10,
    country: str | None = None,
    language: str | None = "english",
    start_date: str | None = None,
    end_date: str | None = None,
):
    """
    Searches for news articles based on a query, and returns the top 10 results by defaults.

    Args:
        query (str | None, optional): Search Query for News. Defaults to None.
        max_results (int, optional): Maximum number of results to show. Defaults to 10.
        country (str | None, optional): Country domain for news channel. Defaults to None.
        language (str | None, optional): Language for search results. Defaults to english.
        start_date (str | None, optional): Date of the format YYYY-MM-DD. Defaults to None.
        end_date (str | None, optional): Date of the format YYYY-MM-DD. Defaults to None.

    Returns:
        _type_: _description_
    """
    if start_date is not None:
        start_date = tuple(map(int, start_date.split("-")))
    if end_date is not None:
        end_date = tuple(map(int, end_date.split("-")))
    new_rss_feed = GNews(
        max_results=max_results,
        country=country,
        language=language,
    )
    if start_date is not None:
        new_rss_feed.start_date = start_date
    if end_date is not None:
        new_rss_feed.end_date = end_date
    results = new_rss_feed.get_news(query)
    results = [get_article(result["url"]) for result in results]
    return results


@app.get("/read_article/{url:path}")
def get_article(url: str):
    """Provided an URL, this function returns the full article as text"""
    google_news = GNews()
    results = google_news.get_full_article(url)
    output = {
        "title": results.title if results.title else None,
        "text": results.text if results.text else None,
        "url": results.url if results.url else None,
        "date": (
            results.publish_date.year,
            results.publish_date.month,
            results.publish_date.day,
        )
        if results.publish_date
        else None,
    }
    return output


if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
