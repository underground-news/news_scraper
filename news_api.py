import requests
from bs4 import BeautifulSoup
from gnews import GNews
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

google_news = GNews()
google_news.max_results = 50  # number of responses across a keyword
google_news.country = "United Kingdom"  # News from a specific country
google_news.language = "english"  # News in a specific language
google_news.start_date = (2022, 2, 13)  # Search from 1st Jan 2020
google_news.end_date = (2022, 2, 15)  # Search until 1st March 2020


class QueryParams(BaseModel):
    max_results: int = 50
    country: str | None = None
    language: str | None = None
    start_date: tuple[int, int, int] | None = None
    end_date: tuple[int, int, int] | None = None


@app.get("/search_results/{query}}")
def get_news(
    query: str | None = None,
    max_results: int = 50,
    country: str | None = None,
    language: str | None = None,
    start_date: tuple[int, int, int] | None = None,
    end_date: tuple[int, int, int] | None = None,
):
    new_rss_feed = GNews(
        max_results=max_results,
        country=country,
        language=language,
        start_date=start_date,
        end_date=end_date,
    )

    return new_rss_feed.get_news(query)


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
    uvicorn.run("news_api:app", host="localhost", port=8000, reload=True)
