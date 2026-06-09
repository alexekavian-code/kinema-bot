import json
import os

FAVORITES_FILE = "favorites.json"


def _load() -> dict:
    if os.path.exists(FAVORITES_FILE):
        with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save(data: dict):
    with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_favorites(user_id: int) -> list[dict]:
    data = _load()
    return data.get(str(user_id), [])


def add_favorite(user_id: int, movie: dict) -> bool:
    data = _load()
    key = str(user_id)
    if key not in data:
        data[key] = []
    movie_id = movie.get("id")
    if any(f["id"] == movie_id for f in data[key]):
        return False  # уже есть
    data[key].append({
        "id": movie_id,
        "title": movie.get("title", "?"),
        "year": movie.get("release_date", "")[:4] or "?",
        "rating": movie.get("vote_average", 0),
    })
    _save(data)
    return True


def remove_favorite(user_id: int, movie_id: int):
    data = _load()
    key = str(user_id)
    if key in data:
        data[key] = [f for f in data[key] if f["id"] != movie_id]
        _save(data)
