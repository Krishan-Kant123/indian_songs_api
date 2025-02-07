from fastapi import FastAPI, Query
import requests
from bs4 import BeautifulSoup
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to specific domains if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



HEADERS = {
     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}


def scrape_pagalfree_search(query: str):
    url = f"https://pagalfree.com/search/{query}"
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        return {"error": "Failed to retrieve the webpage"}

    soup = BeautifulSoup(response.text, "html.parser")
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

def scrape_song_details(url: str):
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        return {"error": "Failed to retrieve the webpage"}

    soup = BeautifulSoup(response.text, "html.parser")
    
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


def scrape_homepage():
    url = "https://pagalfree.com/"
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        return {"error": "Failed to retrieve the webpage"}

    soup = BeautifulSoup(response.text, "html.parser")
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


@app.get("/")
def main():
    return "hii"

@app.get("/search/")
def search_songs(query: str = Query(..., description="Enter song name to search")):
    return scrape_pagalfree_search(query)


@app.get("/song-details/")
def get_song_details(url: str = Query(..., description="Enter the song URL")):
    return scrape_song_details(url)


@app.get("/homepage/")
def get_homepage_songs():
    return scrape_homepage()
