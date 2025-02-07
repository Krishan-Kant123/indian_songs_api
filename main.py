from fastapi import FastAPI, Query
import httpx
from fastapi.responses import Response
from bs4 import BeautifulSoup
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
import socket

# Middleware for CORS
middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*']
    )
]

app = FastAPI(middleware=middleware)

# Headers to mimic a real browser
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}


# Function to resolve IPv4 (Prevents IPv6 issues)
def get_ipv4_url(url: str) -> str:
    domain = url.replace("https://", "").replace("http://", "").split("/")[0]
    ip = socket.gethostbyname(domain)
    return url.replace(domain, ip, 1)


# Async function for making requests
async def fetch_data(url: str):
    ipv4_url = get_ipv4_url(url)  # Convert to IPv4

    async with httpx.AsyncClient() as client:
        response = await client.get(ipv4_url, headers=headers, follow_redirects=True)

    if response.status_code != 200:
        return {"error": f"Failed to retrieve the webpage. Status: {response.status_code}"}

    return response.text


# Scrape PagalFree search results
async def scrape_pagalfree_search(query: str):
    url = f"https://pagalfree.com/search/{query}"
    page_content = await fetch_data(url)
    
    if isinstance(page_content, dict):  # Error handling
        return page_content

    soup = BeautifulSoup(page_content, "html.parser")
    music_items = soup.find_all("div", class_="main_page_category_music_txt")

    songs_data = []
    seen_songs = set()

    for item in music_items:
        song_name = item.find("b").text.strip() if item.find("b") else None
        artist_info = item.find_all("div")[1].text.strip() if len(item.find_all("div")) > 1 else None
        song_url = item.find_parent("a")["href"] if item.find_parent("a") else None
        img_url = item.find_previous("div", class_="main_page_category_music_img").find("img")["src"] if item.find_previous("div", class_="main_page_category_music_img") else None

        if song_name and song_name not in seen_songs:
            seen_songs.add(song_name)
            songs_data.append({
                "song_name": song_name,
                "singers": artist_info,
                "song_url": song_url,
                "img_url": img_url
            })

    return songs_data


# Scrape song details
async def scrape_song_details(url: str):
    page_content = await fetch_data(url)

    if isinstance(page_content, dict):  # Error handling
        return page_content

    soup = BeautifulSoup(page_content, "html.parser")
    
    song_name = soup.find("div", class_="main_page_category_div").text.strip() if soup.find("div", class_="main_page_category_div") else None
    img_url = soup.find("div", class_="col-lg-3 col-md-3 col-sm-12 col-xs-12").find("img")["src"] if soup.find("div", class_="col-lg-3 col-md-3 col-sm-12 col-xs-12") else None
    album_info = soup.find_all("div", class_="col-lg-9 col-md-9 col-sm-6 col-xs-8")
    
    album_name = album_info[0].text.strip() if len(album_info) > 0 else None
    artist_name = album_info[1].text.strip() if len(album_info) > 1 else None
    audio_source = soup.find("audio").find("source")["src"] if soup.find("audio") else None

    return {
        "song_name": song_name,
        "singers": artist_name,
        "album": album_name,
        "img_url": img_url,
        "audio_source": audio_source
    }


# Scrape homepage songs
async def scrape_homepage():
    url = "https://pagalfree.com/"
    page_content = await fetch_data(url)

    if isinstance(page_content, dict):  # Error handling
        return page_content

    soup = BeautifulSoup(page_content, "html.parser")
    categories = soup.find_all("div", class_="main_page_category_div")
    music_data = {}

    for category in categories:
        category_name = category.find("h4", class_="heading").text.strip()
        songs = category.find_all_next("a", href=True)
        songs_info = []

        for song in songs:
            song_url = song["href"]
            song_div = song.find("div", class_="main_page_category_music")
            if not song_div:
                continue

            img_src = song_div.find("img")["src"] if song_div.find("img") else None
            song_txt = song_div.find("div", class_="main_page_category_music_txt")
            song_title = song_txt.find("b").text.strip() if song_txt and song_txt.find("b") else None
            artist_info = song_txt.find_all("div")[1].text.strip() if song_txt and len(song_txt.find_all("div")) > 1 else None

            songs_info.append({
                "song_title": song_title,
                "artist_info": artist_info,
                "img_src": img_src,
                "song_url": song_url
            })

        music_data[category_name] = songs_info

    return music_data


# API Endpoints
@app.get("/")
def main():
    return {"message": "Hello, FastAPI!"}


@app.get("/search/")
async def search_songs(query: str = Query(..., description="Enter song name to search")):
    return await scrape_pagalfree_search(query)


@app.get("/song-details/")
async def get_song_details(url: str = Query(..., description="Enter the song URL")):
    return await scrape_song_details(url)


@app.get("/homepage/")
async def get_homepage_songs():
    return await scrape_homepage()
