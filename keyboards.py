from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from tmdb import GENRES, STUDIOS, COUNTRIES, DECADES


def main_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🎭 По жанру", callback_data="mode:genre")
    builder.button(text="🔍 Поиск по названию", callback_data="mode:search")
    builder.button(text="🎬 По актёру", callback_data="mode:actor")
    builder.button(text="🏢 Жанр + Студия", callback_data="mode:genre_studio")
    builder.button(text="🌍 По стране", callback_data="mode:country")
    builder.button(text="⭐️ Топ по десятилетию", callback_data="mode:decade")
    builder.button(text="❤️ Моё избранное", callback_data="favorites:show")
    builder.adjust(2)
    return builder.as_markup()


def genres_kb(prefix: str = "genre") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for name, gid in GENRES.items():
        builder.button(text=name, callback_data=f"{prefix}:{gid}")
    builder.button(text="🔀 Любой жанр", callback_data=f"{prefix}:any")
    builder.adjust(2)
    return builder.as_markup()


def studios_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for name, sid in STUDIOS.items():
        builder.button(text=name, callback_data=f"studio:{sid}")
    builder.button(text="🔀 Любая студия", callback_data="studio:any")
    builder.adjust(2)
    return builder.as_markup()


def countries_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for name, code in COUNTRIES.items():
        builder.button(text=name, callback_data=f"country:{code}")
    builder.adjust(2)
    return builder.as_markup()


def decades_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for name in DECADES.keys():
        builder.button(text=name, callback_data=f"decade:{name}")
    builder.adjust(2)
    return builder.as_markup()


def results_kb(page: int, has_next: bool, movie_id: int = 0) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if page > 1:
        builder.button(text="⬅️ Назад", callback_data=f"page:{page - 1}")
    if has_next:
        builder.button(text="➡️ Ещё фильм", callback_data=f"page:{page + 1}")
    if movie_id:
        builder.button(text="❤️ В избранное", callback_data=f"fav:add:{movie_id}")
        builder.button(text="🎯 Похожие фильмы", callback_data=f"similar:{movie_id}")
    builder.button(text="📢 Канал Кинема", url="https://t.me/kinema")
    builder.button(text="🔄 Новый поиск", callback_data="restart")
    builder.adjust(2)
    return builder.as_markup()


def search_results_kb(movies: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for m in movies:
        title = m.get("title", "?")
        year = m.get("release_date", "")[:4] or "?"
        builder.button(
            text=f"{title} ({year})",
            callback_data=f"pick:{m['id']}"
        )
    builder.button(text="🔄 Новый поиск", callback_data="restart")
    builder.adjust(1)
    return builder.as_markup()


def favorites_kb(favorites: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for fav in favorites:
        builder.button(
            text=f"🎬 {fav['title']} ({fav['year']})",
            callback_data=f"fav:open:{fav['id']}"
        )
    builder.button(text="🔄 Новый поиск", callback_data="restart")
    builder.adjust(1)
    return builder.as_markup()
