import os
import aiohttp
from typing import Optional

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"
TMDB_LANG = "ru-RU"

GENRES = {
    "🎭 Драма": 18,
    "😂 Комедия": 35,
    "💥 Боевик": 28,
    "🔪 Триллер": 53,
    "👻 Ужасы": 27,
    "❤️ Мелодрама": 10749,
    "🚀 Фантастика": 878,
    "🧙 Фэнтези": 14,
    "🕵️ Криминал": 80,
    "🎬 Анимация": 16,
    "📚 Документальный": 99,
    "🎵 Мюзикл": 10402,
}

STUDIOS = {
    "Marvel Studios": 420,
    "Warner Bros.": 174,
    "Universal Pictures": 33,
    "Paramount Pictures": 4,
    "Columbia Pictures": 5,
    "20th Century Studios": 25,
    "Disney": 2,
    "A24": 41077,
    "Pixar": 3,
    "DreamWorks": 521,
}

COUNTRIES = {
    "🇺🇸 США": "US",
    "🇷🇺 Россия": "RU",
    "🇬🇧 Великобритания": "GB",
    "🇫🇷 Франция": "FR",
    "🇩🇪 Германия": "DE",
    "🇮🇹 Италия": "IT",
    "🇯🇵 Япония": "JP",
    "🇰🇷 Корея": "KR",
    "🇪🇸 Испания": "ES",
    "🇮🇳 Индия": "IN",
}

DECADES = {
    "2020-е": ("2020-01-01", "2029-12-31"),
    "2010-е": ("2010-01-01", "2019-12-31"),
    "2000-е": ("2000-01-01", "2009-12-31"),
    "1990-е": ("1990-01-01", "1999-12-31"),
    "1980-е": ("1980-01-01", "1989-12-31"),
    "До 1980": ("1900-01-01", "1979-12-31"),
}


async def search_person(name: str) -> Optional[int]:
    async with aiohttp.ClientSession() as session:
        url = f"{TMDB_BASE_URL}/search/person"
        params = {"api_key": TMDB_API_KEY, "query": name, "language": TMDB_LANG}
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            results = data.get("results", [])
            if results:
                return results[0]["id"]
    return None


async def search_movie_by_title(title: str) -> list[dict]:
    async with aiohttp.ClientSession() as session:
        url = f"{TMDB_BASE_URL}/search/movie"
        params = {"api_key": TMDB_API_KEY, "query": title, "language": TMDB_LANG}
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            return data.get("results", [])[:10]


async def get_movie_by_id(movie_id: int) -> Optional[dict]:
    async with aiohttp.ClientSession() as session:
        url = f"{TMDB_BASE_URL}/movie/{movie_id}"
        params = {"api_key": TMDB_API_KEY, "language": TMDB_LANG}
        async with session.get(url, params=params) as resp:
            if resp.status == 200:
                return await resp.json()
    return None


async def get_similar_movies(movie_id: int) -> list[dict]:
    async with aiohttp.ClientSession() as session:
        url = f"{TMDB_BASE_URL}/movie/{movie_id}/similar"
        params = {"api_key": TMDB_API_KEY, "language": TMDB_LANG}
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            return data.get("results", [])[:5]


async def get_movies(
    genre_id: Optional[int] = None,
    person_id: Optional[int] = None,
    studio_id: Optional[int] = None,
    country_code: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    page: int = 1,
) -> list[dict]:
    async with aiohttp.ClientSession() as session:
        url = f"{TMDB_BASE_URL}/discover/movie"
        params = {
            "api_key": TMDB_API_KEY,
            "language": TMDB_LANG,
            "sort_by": "vote_average.desc",
            "vote_count.gte": 200,
            "page": page,
        }
        if genre_id:
            params["with_genres"] = genre_id
        if person_id:
            params["with_people"] = person_id
        if studio_id:
            params["with_companies"] = studio_id
        if country_code:
            params["with_origin_country"] = country_code
        if date_from:
            params["primary_release_date.gte"] = date_from
        if date_to:
            params["primary_release_date.lte"] = date_to

        async with session.get(url, params=params) as resp:
            data = await resp.json()
            return data.get("results", [])


def format_movie(movie: dict, show_share_btn: bool = True) -> str:
    title = movie.get("title", "Без названия")
    original_title = movie.get("original_title", "")
    year = movie.get("release_date", "")[:4] if movie.get("release_date") else "?"
    rating = movie.get("vote_average", 0)
    overview = movie.get("overview", "Описание недоступно.")
    movie_id = movie.get("id", "")
    stars = "⭐" * round(rating / 2)

    text = (
        f"🎬 <b>{title}</b>"
        + (f" / <i>{original_title}</i>" if original_title != title else "")
        + f"\n📅 {year}  |  {stars} <b>{rating:.1f}</b>/10\n\n"
        + f"📖 {overview[:400]}{'...' if len(overview) > 400 else ''}\n\n"
        + f"<i>🔗 tmdb.org/movie/{movie_id}</i>"
    )
    return text


def get_poster_url(movie: dict) -> Optional[str]:
    poster = movie.get("poster_path")
    if poster:
        return f"{TMDB_IMAGE_BASE}{poster}"
    return None
