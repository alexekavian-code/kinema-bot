import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from states import SearchStates
from keyboards import main_menu_kb, genres_kb, studios_kb, results_kb
from tmdb import get_movies, search_person, format_movie, get_poster_url, GENRES, STUDIOS

router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🎬 <b>Добро пожаловать в Кинему!</b>\n\n"
        "Я помогу тебе найти идеальный фильм.\n"
        "Выбери, как хочешь искать:",
        parse_mode="HTML",
        reply_markup=main_menu_kb(),
    )
    await state.set_state(SearchStates.choosing_mode)


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "🎬 <b>Кинема — бот для поиска фильмов</b>\n\n"
        "🔍 <b>Режимы поиска:</b>\n"
        "• По жанру\n"
        "• Жанр + актёр\n"
        "• Жанр + студия\n"
        "• Только актёр\n\n"
        "📡 Данные берутся из базы TMDB.\n"
        "/start — начать заново",
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("mode:"))
async def choose_mode(callback: CallbackQuery, state: FSMContext):
    mode = callback.data.split(":")[1]
    await state.update_data(mode=mode, genre_id=None, person_id=None, studio_id=None)
    await callback.message.edit_text(
        "🎭 Выбери жанр:",
        reply_markup=genres_kb("genre"),
    )
    await state.set_state(SearchStates.choosing_genre)
    await callback.answer()


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
            "🎬 Введи имя актёра или режиссёра:\n"
            "<i>(например: Леонардо ДиКаприо)</i>",
            parse_mode="HTML",
        )
        await state.set_state(SearchStates.entering_actor)
    elif mode == "genre_studio":
        await callback.message.edit_text(
            "🏢 Выбери студию:",
            reply_markup=studios_kb(),
        )
        await state.set_state(SearchStates.choosing_studio)
    elif mode == "actor":
        await callback.message.edit_text(
            "🎬 Введи имя актёра или режиссёра:\n"
            "<i>(например: Квентин Тарантино)</i>",
            parse_mode="HTML",
        )
        await state.set_state(SearchStates.entering_actor)
    await callback.answer()


@router.message(SearchStates.entering_actor)
async def enter_actor(message: Message, state: FSMContext):
    name = message.text.strip()
    searching_msg = await message.answer(f"🔍 Ищу <b>{name}</b>...", parse_mode="HTML")
    person_id = await search_person(name)
    if not person_id:
        await searching_msg.edit_text(
            f"😕 Не нашёл человека с именем <b>{name}</b>.\n"
            "Попробуй написать иначе или на английском:",
            parse_mode="HTML",
        )
        return
    await state.update_data(person_id=person_id, person_name=name)
    await searching_msg.delete()
    await show_results(message, state, page=1, edit=False)
    await state.set_state(SearchStates.showing_results)


@router.callback_query(SearchStates.choosing_studio, F.data.startswith("studio:"))
async def choose_studio(callback: CallbackQuery, state: FSMContext):
    raw = callback.data.split(":")[1]
    studio_id = None if raw == "any" else int(raw)
    await state.update_data(studio_id=studio_id)
    await show_results(callback.message, state, page=1, edit=True)
    await state.set_state(SearchStates.showing_results)
    await callback.answer()


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


async def show_results(message: Message, state: FSMContext, page: int, edit: bool = False):
    data = await state.get_data()
    genre_id = data.get("genre_id")
    person_id = data.get("person_id")
    studio_id = data.get("studio_id")

    movies = await get_movies(genre_id=genre_id, person_id=person_id, studio_id=studio_id, page=page)

    if not movies:
        text = "😕 По твоим фильтрам ничего не нашлось. Попробуй другие параметры."
        kb = results_kb(page=1, has_next=False)
        if edit:
            await message.edit_text(text, reply_markup=kb)
        else:
            await message.answer(text, reply_markup=kb)
        return

    idx = (page - 1) % len(movies)
    movie = movies[idx]
    await state.update_data(current_page=page)

    text = format_movie(movie)
    poster_url = get_poster_url(movie)
    kb = results_kb(page=page, has_next=True)

    try:
        if poster_url:
            if edit:
                await message.edit_text(text, parse_mode="HTML", reply_markup=kb)
            else:
                await message.answer_photo(
                    photo=poster_url,
                    caption=text,
                    parse_mode="HTML",
                    reply_markup=kb,
                )
        else:
            if edit:
                await message.edit_text(text, parse_mode="HTML", reply_markup=kb)
            else:
                await message.answer(text, parse_mode="HTML", reply_markup=kb)
    except Exception as e:
        logger.error(f"Ошибка при отправке: {e}")
        await message.answer(text, parse_mode="HTML", reply_markup=kb)
