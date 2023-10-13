import requests
import json
from bs4 import BeautifulSoup
from gnews import GNews
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

import vertexai
from vertexai.language_models import TextGenerationModel


vertexai.init(project="merantix-genai23ber-9502", location="us-central1")
parameters = {
    "candidate_count": 1,
    "max_output_tokens": 1024,
    "temperature": 0.2,
    "top_p": 0.8,
    "top_k": 40,
}
model = TextGenerationModel.from_pretrained("text-bison")


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
    start_date: str | None = "2012-01-01",
    end_date: str | None = "2023-10-12",
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
    results = [get_article(result["url"].split("continue=")[-1]) for result in results]
    return results


@app.get("/search_string_from_article/")
def get_search_string(article: str):
    prompt = (
        article
        + """
    ----
    Given the above news article, give me a search string that I can use to search for other articles on this topic. """
    )

    response = model.predict(prompt, **parameters)
    return response


@app.get("/score/")
def do_the_prediction(article1: str):
    prompt_text = (
        article1
        + """
    ---
    Score the two articles, if there are two, or the single article if there is only one based on the below <Scoring Criteria>, giving
    each criteria a score, a high score means a strong bias on the criteria, low
    score means little bias on the criteria. 

    <Scoring Criteria>:
        - **Word Choice and Tone**: Analyzing the words and tone used to see if they are neutral or emotionally charged to favor a certain perspective.
        - **Framing**: Assessing how the news story is framed to identify if it presents a particular viewpoint or narrative.
        - **Attribution and Sources**: Evaluating the variety and credibility of the sources cited, and whether they represent diverse perspectives.
        - **Omission of Information**: Checking for any crucial information that is left out, which could help in understanding the complete story.
        - **Misleading Statistics**: Evaluating the accuracy and representation of statistics to ensure they are not misleading or taken out of context.
        - **Balance**: Checking if a news story presents multiple sides of an issue or predominantly favors one side.
        - **Context**: Ensuring the news provides enough background information for readers to understand the issue.
        - **Source Diversity**: Looking at the range and diversity of the sources cited in the news story.
        - **Headline Accuracy**: Analyzing if the headline accurately represents the content of the article.
        - **Use of Expertise**: Evaluating whether the article relies on recognized experts and authorities.
        - **Transparency**: Checking for transparency about the news outlet’s processes, funding, and any potential conflicts of interest.
        - **Historical Accuracy**: Evaluating whether historical facts are accurately presented and not distorted.
        - **Image and Graphic Representation**: Assessing if visuals are used in a fair and accurate manner, or if they are manipulated to mislead.
        - **Editorial Policies**: Understanding the editorial policies of the news outlet, including how they handle corrections and responses to criticism.
        - **Comparative Analysis**: Comparing the coverage of the same issue across different news outlets to identify inconsistencies or biases.

    For each article, first decide which 6 of the above <Scoring Criteria> are the most relevant. Then, create output where your output should be formatted as JSON. It should contain an array with one element for each article and each element should contain each one of the 5 <Scoring Criteria> you deemed relvant as a key (replace spaces by underscore) and the value should be the score (from 1-10). 
    If only one article is provided then the array should only contain one element.
    Do not add any additional strings or characters to the output so that the output can be parsed directly with the python json parser function json.loads().
    """
    )
    response = model.predict(prompt_text, **parameters)
    te = response.text
    tt = te.split("[")[1].split("]")[0]
    x = json.loads(tt)
    return f"{x}"


@app.get("/compare/")
def do_the_prediction(article1: str, article2: str = ""):
    prompt_text = (
        article1
        + """
    ------
    """
        + article2
        + """
    ---
    Score the two articles, if there are two, or the single article if there is only one based on the below <Scoring Criteria>, giving
    each criteria a score, a high score means a strong bias on the criteria, low
    score means little bias on the criteria. 

    <Scoring Criteria>:
        - **Word Choice and Tone**: Analyzing the words and tone used to see if they are neutral or emotionally charged to favor a certain perspective.
        - **Framing**: Assessing how the news story is framed to identify if it presents a particular viewpoint or narrative.
        - **Attribution and Sources**: Evaluating the variety and credibility of the sources cited, and whether they represent diverse perspectives.
        - **Omission of Information**: Checking for any crucial information that is left out, which could help in understanding the complete story.
        - **Misleading Statistics**: Evaluating the accuracy and representation of statistics to ensure they are not misleading or taken out of context.
        - **Balance**: Checking if a news story presents multiple sides of an issue or predominantly favors one side.
        - **Context**: Ensuring the news provides enough background information for readers to understand the issue.
        - **Source Diversity**: Looking at the range and diversity of the sources cited in the news story.
        - **Headline Accuracy**: Analyzing if the headline accurately represents the content of the article.
        - **Use of Expertise**: Evaluating whether the article relies on recognized experts and authorities.
        - **Transparency**: Checking for transparency about the news outlet’s processes, funding, and any potential conflicts of interest.
        - **Historical Accuracy**: Evaluating whether historical facts are accurately presented and not distorted.
        - **Image and Graphic Representation**: Assessing if visuals are used in a fair and accurate manner, or if they are manipulated to mislead.
        - **Editorial Policies**: Understanding the editorial policies of the news outlet, including how they handle corrections and responses to criticism.
        - **Comparative Analysis**: Comparing the coverage of the same issue across different news outlets to identify inconsistencies or biases.

    For each article, first decide which 6 of the above <Scoring Criteria>  are the most relevant. Then, create output where your output should be formatted as JSON. It should contain an array with one element for each article and each element should contain each one of the 5 <Scoring Criteria> you deemed relvant as a key (replace spaces by underscore) and the value should be the score (from 1-10). 
    If only one article is provided then the array should only contain one element.
    Do not add any additional strings or characters to the output so that the output can be parsed directly with the python json parser function json.loads().
    """
    )
    response = model.predict(prompt_text, **parameters)
    te = response.text
    tt = te.split("[")[1].split("]")[0]
    tt = "[" + tt + "]"
    x = json.loads(tt)
    return f"{x}"


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
