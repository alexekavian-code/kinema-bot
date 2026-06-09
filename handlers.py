import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from states import SearchStates
from keyboards import (
    main_menu_kb, genres_kb, studios_kb, countries_kb,
    decades_kb, results_kb, search_results_kb, favorites_kb
)
from tmdb import (
    get_movies, search_person, search_movie_by_title, get_movie_by_id,
    get_similar_movies, format_movie, get_poster_url, DECADES
)
from favorites import get_favorites, add_favorite, remove_favorite

router = Router()
logger = logging.getLogger(__name__)

CHANNEL = "@kinema"


# ─── /start ───────────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🎬 <b>Добро пожаловать в Кинему!</b>\n\n"
        "Я помогу найти идеальный фильм для любого настроения.\n\n"
        "📢 Подпишись на канал: " + CHANNEL,
        parse_mode="HTML",
        reply_markup=main_menu_kb(),
    )
    await state.set_state(SearchStates.choosing_mode)


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "🎬 <b>Кинема — бот для поиска фильмов</b>\n\n"
        "🔍 Поиск по названию\n"
        "🎭 По жанру\n"
        "🎬 По актёру / режиссёру\n"
        "🏢 По студии\n"
        "🌍 По стране производства\n"
        "⭐️ Топ по десятилетию\n"
        "❤️ Избранное\n"
        "🎯 Похожие фильмы\n\n"
        "📢 Канал: " + CHANNEL + "\n"
        "/start — главное меню",
        parse_mode="HTML",
    )


# ─── Выбор режима ─────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("mode:"))
async def choose_mode(callback: CallbackQuery, state: FSMContext):
    mode = callback.data.split(":")[1]
    await state.update_data(mode=mode, genre_id=None, person_id=None,
                            studio_id=None, country_code=None,
                            date_from=None, date_to=None)

    if mode == "search":
        await callback.message.edit_text(
            "🔍 Введи название фильма:",
            parse_mode="HTML",
        )
        await state.set_state(SearchStates.entering_search)

    elif mode == "actor":
        await callback.message.edit_text(
            "🎬 Введи имя актёра или режиссёра:\n<i>(например: Кристофер Нолан)</i>",
            parse_mode="HTML",
        )
        await state.set_state(SearchStates.entering_actor)

    elif mode == "country":
        await callback.message.edit_text("🌍 Выбери страну:", reply_markup=countries_kb())
        await state.set_state(SearchStates.choosing_country)

    elif mode == "decade":
        await callback.message.edit_text("⭐️ Выбери десятилетие:", reply_markup=decades_kb())
        await state.set_state(SearchStates.choosing_decade)

    else:
        await callback.message.edit_text("🎭 Выбери жанр:", reply_markup=genres_kb("genre"))
        await state.set_state(SearchStates.choosing_genre)

    await callback.answer()


# ─── Поиск по названию ────────────────────────────────────────────────────────

@router.message(SearchStates.entering_search)
async def enter_search(message: Message, state: FSMContext):
    title = message.text.strip()
    msg = await message.answer(f"🔍 Ищу <b>{title}</b>...", parse_mode="HTML")
    movies = await search_movie_by_title(title)
    if not movies:
        await msg.edit_text("😕 Ничего не найдено. Попробуй другое название.")
        return
    await msg.edit_text(
        f"🎬 Нашёл {len(movies)} фильмов. Выбери:",
        reply_markup=search_results_kb(movies),
    )
    await state.set_state(SearchStates.showing_results)


@router.callback_query(F.data.startswith("pick:"))
async def pick_movie(callback: CallbackQuery, state: FSMContext):
    movie_id = int(callback.data.split(":")[1])
    movie = await get_movie_by_id(movie_id)
    if not movie:
        await callback.answer("Не удалось загрузить фильм")
        return
    await state.update_data(last_movie=movie)
    text = format_movie(movie)
    poster = get_poster_url(movie)
    kb = results_kb(page=1, has_next=False, movie_id=movie_id)
    try:
        if poster:
            await callback.message.answer_photo(photo=poster, caption=text,
                                                 parse_mode="HTML", reply_markup=kb)
        else:
            await callback.message.answer(text, parse_mode="HTML", reply_markup=kb)
    except Exception as e:
        logger.error(e)
        await callback.message.answer(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


# ─── Выбор жанра ──────────────────────────────────────────────────────────────

@router.callback_query(SearchStates.choosing_genre, F.data.startswith("genre:"))
async def choose_genre(callback: CallbackQuery, state: FSMContext):
    raw = callback.data.split(":")[1]
    genre_id = None if raw == "any" else int(raw)
    await state.update_data(genre_id=genre_id)
    data = await state.get_data()
    mode = data.get("mode")

    if mode == "genre":
        await show_results(callback.message, state, page=1, edit=True)
        await state.set_state(SearchStates.showing_results)
    elif mode == "genre_actor":
        await callback.message.edit_text(
            "🎬 Введи имя актёра или режиссёра:", parse_mode="HTML")
        await state.set_state(SearchStates.entering_actor)
    elif mode == "genre_studio":
        await callback.message.edit_text("🏢 Выбери студию:", reply_markup=studios_kb())
        await state.set_state(SearchStates.choosing_studio)
    await callback.answer()


# ─── Ввод актёра ──────────────────────────────────────────────────────────────

@router.message(SearchStates.entering_actor)
async def enter_actor(message: Message, state: FSMContext):
    name = message.text.strip()
    msg = await message.answer(f"🔍 Ищу <b>{name}</b>...", parse_mode="HTML")
    person_id = await search_person(name)
    if not person_id:
        await msg.edit_text(
            f"😕 Не нашёл <b>{name}</b>.\nПопробуй написать на английском:",
            parse_mode="HTML")
        return
    await state.update_data(person_id=person_id, person_name=name)
    await msg.delete()
    await show_results(message, state, page=1, edit=False)
    await state.set_state(SearchStates.showing_results)


# ─── Выбор студии ─────────────────────────────────────────────────────────────

@router.callback_query(SearchStates.choosing_studio, F.data.startswith("studio:"))
async def choose_studio(callback: CallbackQuery, state: FSMContext):
    raw = callback.data.split(":")[1]
    studio_id = None if raw == "any" else int(raw)
    await state.update_data(studio_id=studio_id)
    await show_results(callback.message, state, page=1, edit=True)
    await state.set_state(SearchStates.showing_results)
    await callback.answer()


# ─── Выбор страны ─────────────────────────────────────────────────────────────

@router.callback_query(SearchStates.choosing_country, F.data.startswith("country:"))
async def choose_country(callback: CallbackQuery, state: FSMContext):
    country_code = callback.data.split(":")[1]
    await state.update_data(country_code=country_code)
    await show_results(callback.message, state, page=1, edit=True)
    await state.set_state(SearchStates.showing_results)
    await callback.answer()


# ─── Выбор десятилетия ────────────────────────────────────────────────────────

@router.callback_query(SearchStates.choosing_decade, F.data.startswith("decade:"))
async def choose_decade(callback: CallbackQuery, state: FSMContext):
    decade_name = callback.data.split(":", 1)[1]
    date_from, date_to = DECADES[decade_name]
    await state.update_data(date_from=date_from, date_to=date_to)
    await show_results(callback.message, state, page=1, edit=True)
    await state.set_state(SearchStates.showing_results)
    await callback.answer()


# ─── Избранное ────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "favorites:show")
async def show_favorites(callback: CallbackQuery, state: FSMContext):
    favs = get_favorites(callback.from_user.id)
    if not favs:
        await callback.message.edit_text(
            "❤️ <b>Избранное пусто</b>\n\nДобавляй фильмы кнопкой ❤️ В избранное",
            parse_mode="HTML",
            reply_markup=main_menu_kb(),
        )
    else:
        await callback.message.edit_text(
            f"❤️ <b>Твоё избранное</b> ({len(favs)} фильмов):",
            parse_mode="HTML",
            reply_markup=favorites_kb(favs),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("fav:add:"))
async def add_to_favorites(callback: CallbackQuery, state: FSMContext):
    movie_id = int(callback.data.split(":")[2])
    movie = await get_movie_by_id(movie_id)
    if movie and add_favorite(callback.from_user.id, movie):
        await callback.answer("❤️ Добавлено в избранное!", show_alert=False)
    else:
        await callback.answer("Уже в избранном", show_alert=False)


@router.callback_query(F.data.startswith("fav:open:"))
async def open_favorite(callback: CallbackQuery, state: FSMContext):
    movie_id = int(callback.data.split(":")[2])
    movie = await get_movie_by_id(movie_id)
    if not movie:
        await callback.answer("Не удалось загрузить")
        return
    text = format_movie(movie)
    poster = get_poster_url(movie)
    kb = results_kb(page=1, has_next=False, movie_id=movie_id)
    try:
        if poster:
            await callback.message.answer_photo(photo=poster, caption=text,
                                                 parse_mode="HTML", reply_markup=kb)
        else:
            await callback.message.answer(text, parse_mode="HTML", reply_markup=kb)
    except Exception as e:
        logger.error(e)
    await callback.answer()


# ─── Похожие фильмы ───────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("similar:"))
async def show_similar(callback: CallbackQuery, state: FSMContext):
    movie_id = int(callback.data.split(":")[1])
    movies = await get_similar_movies(movie_id)
    if not movies:
        await callback.answer("Похожих фильмов не найдено", show_alert=True)
        return
    await callback.message.answer(
        "🎯 <b>Похожие фильмы:</b>",
        parse_mode="HTML",
        reply_markup=search_results_kb(movies),
    )
    await callback.answer()


# ─── Пагинация ────────────────────────────────────────────────────────────────

@router.callback_query(SearchStates.showing_results, F.data.startswith("page:"))
async def paginate(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split(":")[1])
    await show_results(callback.message, state, page=page, edit=True)
    await callback.answer()


@router.callback_query(F.data == "restart")
async def restart(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🎬 <b>Новый поиск!</b>\n\nВыбери, как хочешь искать:",
        parse_mode="HTML",
        reply_markup=main_menu_kb(),
    )
    await state.set_state(SearchStates.choosing_mode)
    await callback.answer()


# ─── Показ результатов ────────────────────────────────────────────────────────

async def show_results(message: Message, state: FSMContext, page: int, edit: bool = False):
    data = await state.get_data()
    movies = await get_movies(
        genre_id=data.get("genre_id"),
        person_id=data.get("person_id"),
        studio_id=data.get("studio_id"),
        country_code=data.get("country_code"),
        date_from=data.get("date_from"),
        date_to=data.get("date_to"),
        page=page,
    )

    if not movies:
        text = "😕 По твоим фильтрам ничего не нашлось."
        kb = results_kb(page=1, has_next=False)
        if edit:
            await message.edit_text(text, reply_markup=kb)
        else:
            await message.answer(text, reply_markup=kb)
        return

    idx = (page - 1) % len(movies)
    movie = movies[idx]
    movie_id = movie.get("id", 0)

    text = format_movie(movie)
    poster = get_poster_url(movie)
    kb = results_kb(page=page, has_next=True, movie_id=movie_id)

    try:
        if poster:
            if edit:
                await message.edit_text(text, parse_mode="HTML", reply_markup=kb)
            else:
                await message.answer_photo(photo=poster, caption=text,
                                            parse_mode="HTML", reply_markup=kb)
        else:
            if edit:
                await message.edit_text(text, parse_mode="HTML", reply_markup=kb)
            else:
                await message.answer(text, parse_mode="HTML", reply_markup=kb)
    except Exception as e:
        logger.error(f"Ошибка отправки: {e}")
        await message.answer(text, parse_mode="HTML", reply_markup=kb)
