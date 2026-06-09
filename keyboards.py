from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from tmdb import GENRES, STUDIOS


def main_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🎭 По жанру", callback_data="mode:genre")
    builder.button(text="🎭 Жанр + 🎬 Актёр", callback_data="mode:genre_actor")
    builder.button(text="🏢 Жанр + Студия", callback_data="mode:genre_studio")
    builder.button(text="🎬 Только актёр", callback_data="mode:actor")
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


def results_kb(page: int, has_next: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if page > 1:
        builder.button(text="⬅️ Назад", callback_data=f"page:{page - 1}")
    if has_next:
        builder.button(text="➡️ Ещё фильм", callback_data=f"page:{page + 1}")
    builder.button(text="🔄 Новый поиск", callback_data="restart")
    builder.adjust(2)
    return builder.as_markup()
