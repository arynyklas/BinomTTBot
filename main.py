from aiogram import Bot, Dispatcher, types, exceptions
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler

from asyncio import sleep

from edupage import Lesson, TimeTableInfo, TimeTable
from db import User, init_db
from keyboards import Keyboards
from utils import read_json, save_json
from basic_data import TEXTS
from config import config, save_config

from copy import deepcopy
from dataclasses import asdict
from hashlib import md5
from traceback import format_exc

from typing import Dict, List, Optional, Tuple, Union


keyboards: Keyboards


bot: Bot = Bot(
    token = config.bot_token,
    parse_mode = types.ParseMode.HTML
)

dp: Dispatcher = Dispatcher(
    bot = bot
)


timetable_api: TimeTable = TimeTable(
    storage_path = config.timetable.storage_filename,
    response_path = config.timetable.response_filename
)


classes_by_timetable_and_id_to_name: Dict[str, Dict[str, Dict[str, Union[str, int]]]]
class_ids: List[str] = []
class_names: Dict[str, Tuple[str, str]] = {}

known_class_ids: List[str] = []
known_class_names: List[str] = []

for class_name, class_ in config.timetable.classes.items():
    known_class_names.append(known_class_names)
    known_class_ids.append(class_["id"])


tables: Dict[str, Dict[str, Dict[str, dict]]] = {}

classes_timetables: Dict[str, Dict[str, Dict[str, Dict[str, Dict[str, str]]]]]

try:
    classes_timetables = read_json(
        filename = config.timetable.classes_filename
    )

except:
    classes_timetables = {
        timetable_number: {}
        for timetable_number in config.timetable.numbers
    }

    save_json(
        filename = config.timetable.classes_filename,
        data = classes_timetables
    )


class UsersMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        super(UsersMiddleware, self).__init__()

    async def on_process_message(self, message: types.Message, data: dict) -> None:
        if message.chat.type != types.ChatType.PRIVATE:
            raise CancelHandler

        user_id: int = message.chat.id

        if not await User.find_one(
            User.user_id == user_id
        ):
            await User(
                user_id = user_id
            ).insert()


def get_timetable_for_class(timetable_number: str, class_id: str) -> str:
    class_: dict = config.timetable.classes[classes_by_timetable_and_id_to_name[timetable_number][class_id]]

    class_timetable: Dict[str, Dict[str, Dict[str, str]]] = classes_timetables[timetable_number][class_id]

    tables_: Dict[str, Dict[str, dict]] = tables[timetable_number]

    daysdefs_lessons: Dict[str, Dict[str, str]] = {}

    null_timetable: Dict[str, Dict[str, Union[str, int]]] = {
        period_id: None
        for period_id in tables_["periods"].keys()
    }

    for day_id in class_timetable.keys():
        for period_id, lesson_dict in class_timetable[day_id].items():
            if not lesson_dict:
                daysdefs_lessons[day_id][period_id] = TEXTS["edupage"]["timetable"]["unknown_lesson"].format(
                    period = period["name"],
                    start_time = period["starttime"],
                    end_time = period["endtime"]
                )

                continue

            lesson: Optional[Lesson] = Lesson(**lesson_dict)

            if day_id not in daysdefs_lessons:
                daysdefs_lessons[day_id] = deepcopy(null_timetable)

            int_lesson_period: int = int(lesson.period)

            for i in range(lesson.durationperiods):
                period_id: str = str(int_lesson_period + i)
                period: dict = tables_["periods"][period_id]

                daysdefs_lessons[day_id][period_id] = TEXTS["edupage"]["timetable"]["lesson"].format(
                    period = period["name"],
                    start_time = period["starttime"],
                    end_time = period["endtime"],
                    subject = tables_["subjects"][lesson.subjectid]["name"].strip(),
                    teachers = ", ".join([tables_["teachers"][teacher_id]["lastname"].strip() for teacher_id in lesson.teacherids]),
                    groups = ", ".join([tables_["groups"][group_id]["name"] for group_id in lesson.groupids]).lower(),
                    classrooms = (
                        ", ".join([tables_["classrooms"][classroom_id]["name"].strip().split(" ", 1)[0] for classroom_id in lesson.classroomidss if classroom_id])
                        if lesson.classroomidss and lesson.classroomidss[0] != ""
                        else
                        ", ".join([" | ".join([tables_["classrooms"][classroom_id]["name"].strip().split(" ", 1)[0] for classroom_id in classroom_idss]) for classroom_idss in lesson.classroomidss])
                    )
                )

    daysdefs_lessons = timetable_api.sort(
        class_timetable = daysdefs_lessons,
        not_lesson = True
    )

    daysdefs_lessons__: Dict[str, List[str]] = {}

    for day_id in daysdefs_lessons.keys():
        for period_id, value in daysdefs_lessons[day_id].items():
            if day_id not in daysdefs_lessons__:
                daysdefs_lessons__[day_id] = []

            if value:
                daysdefs_lessons__[day_id].append(value)

            else:
                period: dict = tables_["periods"][period_id]

                daysdefs_lessons__[day_id].append(
                    TEXTS["edupage"]["timetable"]["unknown_lesson"].format(
                        period = period["name"],
                        start_time = period["starttime"],
                        end_time = period["endtime"]
                    )
                )

    return TEXTS["edupage"]["timetable"]["default"].format(
        additional_text = TEXTS["edupage"]["timetable"]["bot"].format(
            class_name = class_["name"]
        ),
        daysdefs = "\n\n".join([
            TEXTS["edupage"]["timetable"]["daysdef"].format(
                daysdef = tables_["daysdefs"][day_id]["name"],
                lessons = "\n".join(lessons)
            )
            for day_id, lessons in daysdefs_lessons__.items()
        ]),
        main_channel_url = config.main_channel_url,
        post_channel_href = (
            TEXTS["edupage"]["timetable"]["url"].format(
                url = class_["bot_channel_url"],
                class_name = class_["name"]
            )
            if class_["channel_id"] != -1
            else
            class_["name"]
        )
    )


@dp.inline_handler()
async def inline_handler(inline_query: types.InlineQuery) -> None:
    class_name: str = inline_query.query.strip()

    if not class_name:
        await inline_query.answer(
            results = [],
            cache_time = config.inline_cache_time
        )

        return

    class_name = class_name.upper()

    if class_name not in class_names:
        await inline_query.answer(
            results = [],
            cache_time = config.inline_cache_time
        )

        return

    timetable_number: str
    class_id: str

    timetable_number, class_id = class_names[class_name]

    class_: dict = config.timetable.classes[class_name]

    await inline_query.answer(
        results = [
            types.InlineQueryResultArticle(
                id = md5(
                    string = class_id.encode("utf-8")
                ).hexdigest(),
                title = TEXTS["edupage"]["timetable"]["inline_title"].format(
                    class_name = class_name
                ),
                input_message_content = types.InputTextMessageContent(
                    message_text = get_timetable_for_class(
                        timetable_number = timetable_number,
                        class_id = class_id
                    ),
                    parse_mode = bot.parse_mode
                ),
                reply_markup = (
                    keyboards.inline_timetable(
                        channel_url = class_["bot_channel_url"]
                    )
                    if class_["bot_channel_url"]
                    else
                    None
                )
            )
        ],
        cache_time = config.inline_cache_time
    )


@dp.callback_query_handler()
async def callback_query_handler(callback_query: types.CallbackQuery) -> None:
    await callback_query.answer()

    args: List[str] = callback_query.data.split("_")
    args_len: int = len(args)

    if args[0] == "timetable":
        if args_len == 2 or args[1] == "class":
            class_id: str = (
                args[1]
                if args_len == 2
                else
                args[2]
            )

            timetable_index: int = (
                0
                if args_len != 4
                else
                (
                    config.timetable.old_numbers[args[3]]
                    if args[3] in config.timetable.old_numbers
                    else
                    config.timetable.numbers.index(args[3])
                )
            )

            timetable_number: str = config.timetable.numbers[timetable_index]

            class_: dict = config.timetable.classes[classes_by_timetable_and_id_to_name[timetable_number][class_id]]

            class_timetable: Dict[str, Dict[str, Dict[str, str]]] = classes_timetables[timetable_number][class_id]

            tables_: Dict[str, Dict[str, dict]] = tables[timetable_number]

            daysdefs_lessons: Dict[str, Dict[str, str]] = {}

            null_timetable: Dict[str, Dict[str, Union[str, int]]] = {
                period_id: None
                for period_id in tables_["periods"].keys()
            }

            for day_id in class_timetable.keys():
                for period_id, lesson_dict in class_timetable[day_id].items():
                    if not lesson_dict:
                        daysdefs_lessons[day_id][period_id] = TEXTS["edupage"]["timetable"]["unknown_lesson"].format(
                            period = period["name"],
                            start_time = period["starttime"],
                            end_time = period["endtime"]
                        )

                        continue

                    lesson: Optional[Lesson] = Lesson(**lesson_dict)

                    if day_id not in daysdefs_lessons:
                        daysdefs_lessons[day_id] = deepcopy(null_timetable)

                    int_lesson_period: int = int(lesson.period)

                    for i in range(lesson.durationperiods):
                        period_id: str = str(int_lesson_period + i)
                        period: dict = tables_["periods"][period_id]

                        daysdefs_lessons[day_id][period_id] = TEXTS["edupage"]["timetable"]["lesson"].format(
                            period = period["name"],
                            start_time = period["starttime"],
                            end_time = period["endtime"],
                            subject = tables_["subjects"][lesson.subjectid]["name"].strip(),
                            teachers = ", ".join([tables_["teachers"][teacher_id]["lastname"].strip() for teacher_id in lesson.teacherids]),
                            groups = ", ".join([tables_["groups"][group_id]["name"] for group_id in lesson.groupids]).lower(),
                            classrooms = (
                                ", ".join([tables_["classrooms"][classroom_id]["name"].strip().split(" ", 1)[0] for classroom_id in lesson.classroomidss if classroom_id])
                                if lesson.classroomidss and lesson.classroomidss[0] != ""
                                else
                                ", ".join([" | ".join([tables_["classrooms"][classroom_id]["name"].strip().split(" ", 1)[0] for classroom_id in classroom_idss]) for classroom_idss in lesson.classroomidss])
                            )
                        )

            daysdefs_lessons = timetable_api.sort(
                class_timetable = daysdefs_lessons,
                not_lesson = True
            )

            daysdefs_lessons__: Dict[str, List[str]] = {}

            for day_id in daysdefs_lessons.keys():
                for period_id, value in daysdefs_lessons[day_id].items():
                    if day_id not in daysdefs_lessons__:
                        daysdefs_lessons__[day_id] = []

                    if value:
                        daysdefs_lessons__[day_id].append(value)

                    else:
                        period: dict = tables_["periods"][period_id]

                        daysdefs_lessons__[day_id].append(
                            TEXTS["edupage"]["timetable"]["unknown_lesson"].format(
                                period = period["name"],
                                start_time = period["starttime"],
                                end_time = period["endtime"]
                            )
                        )

            await callback_query.message.answer(
                text = TEXTS["edupage"]["timetable"]["default"].format(
                    additional_text = TEXTS["edupage"]["timetable"]["bot"].format(
                        class_name = class_["name"]
                    ),
                    daysdefs = "\n\n".join([
                        TEXTS["edupage"]["timetable"]["daysdef"].format(
                            daysdef = tables_["daysdefs"][day_id]["name"],
                            lessons = "\n".join(lessons)
                        )
                        for day_id, lessons in daysdefs_lessons__.items()
                    ]),
                    main_channel_url = config.main_channel_url,
                    post_channel_href = (
                        TEXTS["edupage"]["timetable"]["url"].format(
                            url = class_["bot_channel_url"],
                            class_name = class_["name"]
                        )
                        if class_["channel_id"] != -1
                        else
                        class_["name"]
                    )
                ),
                disable_web_page_preview = True
            )

        elif args[1] == "page":
            page: int = int(args[2])

            classes_markup: types.InlineKeyboardMarkup

            if page > keyboards._max_classes_page:
                classes_markup = keyboards.classes[0]
            else:
                classes_markup = keyboards.classes[page]

            await callback_query.message.edit_reply_markup(
                reply_markup = classes_markup
            )


@dp.message_handler(commands=["start"])
async def bot_start_command_handler(message: types.Message) -> None:
    await message.answer(
        text = TEXTS["start"],
        reply_markup = keyboards.classes[0]
    )


async def admins_notify(text: str) -> None:
    for admin in config.admins:
        admin: int

        try:
            await bot.send_message(
                chat_id = admin,
                text = text
            )

        except exceptions.TelegramAPIError:
            pass


@dp.errors_handler()
async def errors_handler(update: Union[types.Update, None], exception: Exception) -> bool:
    type_: object = type(exception)

    if type_ == exceptions.InvalidQueryID:
        return True

    elif type_ == KeyError and exception.args[0] == "dbiAccessorRes":
        timetables_infos: List[TimeTableInfo] = await timetable_api.get_active_timetables_info()

        await admins_notify(
            text = TEXTS["admins"]["table_rights_changed"]["default"].format(
                timetables = "\n".join([
                    TEXTS["admins"]["table_rights_changed"]["timetable"].format(
                        number = timetable_info.number,
                        text = timetable_info.text
                    )
                    for timetable_info in timetables_infos
                ])
            )
        )

        return True

    await admins_notify(
        text = TEXTS["admins"]["unknown_error"].format(
            traceback = format_exc(),
            update = (
                update.as_json()
                if update
                else
                ""
            )
        )
    )

    return True


dp.middleware.setup(
    middleware = UsersMiddleware()
)


async def timetable_load() -> None:
    global classes_timetables, tables, keyboards

    for timetable_number in config.timetable.numbers:
        classes_timetables_, tables_ = await timetable_api.get_timetables(
            timetable_number = timetable_number
        )

        tables[timetable_number] = tables_

        timetable_api.save_storage()

        for class_id in classes_timetables_.keys():
            for day_id in classes_timetables_[class_id].keys():
                for period_id, lesson in classes_timetables_[class_id][day_id].items():
                    if lesson:
                        classes_timetables_[class_id][day_id][period_id] = asdict(lesson)

        classes_timetables[timetable_number] = classes_timetables_

    save_json(
        filename = config.timetable.classes_filename,
        data = classes_timetables
    )


def _sort_classes(item: Tuple[str, dict]) -> Tuple[int, int]:
    grade, letter = item[0].split()
    return int(grade), TEXTS["alphabet"].index(letter.replace("*", "", 1))

def load_classes(classes: Dict[str, Dict[str, Union[str, int]]], new_timetable_numbers: Optional[List[str]]=None) -> Dict[str, Dict[str, Union[str, int]]]:
    global tables, classes_timetables, classes_by_timetable_and_id_to_name

    for timetable_index, timetable_number in enumerate(deepcopy(config.timetable.numbers), 0):
        if new_timetable_numbers:
            old_table: Dict[str, Dict[str, dict]] = tables.pop(timetable_number)
            old_classes_timetable: Dict[str, Dict[str, Dict[str, Dict[str, str]]]] = classes_timetables.pop(timetable_number)
            old_class_by_timetable_and_id_to_name: Dict[str, Dict[str, Union[str, int]]] = classes_by_timetable_and_id_to_name.pop(timetable_number)
            config.timetable.numbers.remove(timetable_number)

            timetable_number: str = new_timetable_numbers[timetable_index]
            tables[timetable_number] = old_table
            classes_timetables[timetable_number] = old_classes_timetable
            classes_by_timetable_and_id_to_name[timetable_number] = old_class_by_timetable_and_id_to_name
            config.timetable.numbers.append(timetable_number)

        for class_id, class_ in tables[timetable_number]["classes"].items():
            class_name: str = class_["name"].strip()

            class__: dict

            if class_name not in classes:
                class__ = deepcopy(config.clear_class)
                class__["id"] = class_id
                class__["name"] = class_name

                classes_by_timetable_and_id_to_name[timetable_number][class_id] = class_name

                class__["timetable_number"] = timetable_number
                classes[class_name] = class__

            elif classes[class_name]["timetable_number"] != timetable_number:
                class__ = deepcopy(classes[class_name])

                classes_by_timetable_and_id_to_name[timetable_number][class_id] = class_name

                class__["timetable_number"] = timetable_number
                classes[class_name] = class__

    classes = dict(sorted(
        classes.items(),
        key = _sort_classes
    ))

    return classes


async def notifier(seconds: int) -> None:
    global tables

    async def _notifier() -> None:
        for timetable_number in config.timetable.numbers:
            try:
                timetable, tables_ = await timetable_api.get_newest_timetables(
                    timetable_number = timetable_number,
                    old_tables = tables[timetable_number]
                )

            except KeyError as ex:
                if ex.args[0] != "dbiAccessorRes":
                    raise ex

                timetables_infos: List[TimeTableInfo] = (await timetable_api.get_active_timetables_info())[:2]

                # For debug
                await admins_notify(
                    text = "?????? notifier\n\n" + TEXTS["admins"]["table_rights_changed"]["default"].format(
                        timetables = "\n".join([
                            TEXTS["admins"]["table_rights_changed"]["timetable"].format(
                                number = timetable_info.number,
                                text = timetable_info.text
                            )
                            for timetable_info in timetables_infos
                        ])
                    )
                )

                new_timetable_numbers: List[str] = [
                    timetables_info.number
                    for timetables_info in timetables_infos
                ]

                current_classes: Dict[str, Dict[str, Union[str, int]]] = load_classes(
                    classes = config.timetable.classes,
                    new_timetable_numbers = new_timetable_numbers
                )

                config.timetable.classes = {
                    current_class_name: current_class
                    for current_class_name, current_class in current_classes.items()
                    if current_class_name in known_class_names
                }

                config.timetable.numbers = new_timetable_numbers

                save_config(
                    config = config
                )

                config.timetable.classes = current_classes

                keyboards.update_classes(
                    classes = config.timetable.classes
                )

                timetable, tables_ = await timetable_api.get_newest_timetables(
                    timetable_number = timetable_number,
                    old_tables = tables[timetable_number]
                )

            if not timetable:
                continue

            null_timetable: Dict[str, Dict[str, Union[str, int]]] = {
                period_id: None
                for period_id in tables_["periods"].keys()
            }

            for class_id, class_timetable in timetable.items():
                class_timetable_ = timetable_api.sort(
                    class_timetable = class_timetable
                )

                class_timetable = deepcopy(class_timetable_)

                daysdefs_lessons: Dict[str, Dict[str, str]] = {}

                for day_id in class_timetable.keys():
                    for period_id, lesson in class_timetable_[day_id].items():
                        lesson: Union[Lesson, None]

                        if not lesson:
                            daysdefs_lessons[day_id][period_id] = TEXTS["edupage"]["timetable"]["unknown_lesson"].format(
                                period = period["name"],
                                start_time = period["starttime"],
                                end_time = period["endtime"]
                            )

                            continue

                        if day_id not in daysdefs_lessons:
                            daysdefs_lessons[day_id] = deepcopy(null_timetable)

                        int_lesson_period: int = int(lesson.period)

                        for i in range(lesson.durationperiods):
                            period_id: str = str(int_lesson_period + i)
                            period: dict = tables_["periods"][period_id]

                            daysdefs_lessons[day_id][period_id] = TEXTS["edupage"]["timetable"]["lesson"].format(
                                period = period["name"],
                                start_time = period["starttime"],
                                end_time = period["endtime"],
                                subject = tables_["subjects"][lesson.subjectid]["name"].strip(),
                                teachers = ", ".join([tables_["teachers"][teacher_id]["lastname"].strip() for teacher_id in lesson.teacherids]),
                                groups = ", ".join([tables_["groups"][group_id]["name"] for group_id in lesson.groupids]).lower(),
                                classrooms = (
                                    ", ".join([tables_["classrooms"][classroom_id]["name"].strip().split(" ", 1)[0] for classroom_id in lesson.classroomidss])
                                    if lesson.classroomidss and lesson.classroomidss[0] != ""
                                    else
                                    ", ".join([" | ".join([tables_["classrooms"][classroom_id]["name"].strip().split(" ", 1)[0] for classroom_id in classroom_idss]) for classroom_idss in lesson.classroomidss])
                                )
                            )

                        classes_timetables[timetable_number][class_id][day_id][period_id] = asdict(lesson)

                daysdefs_lessons = timetable_api.sort(
                    class_timetable = daysdefs_lessons,
                    not_lesson = True
                )

                daysdefs_lessons__: Dict[str, List[str]] = {}

                for day_id in daysdefs_lessons.keys():
                    for period_id, value in daysdefs_lessons[day_id].items():
                        if day_id not in daysdefs_lessons__:
                            daysdefs_lessons__[day_id] = []

                        daysdefs_lessons__[day_id].append(value)

                is_known_class: bool = class_id in known_class_ids

                class_: dict = (
                    config.timetable.classes[classes_by_timetable_and_id_to_name[timetable_number][class_id]]
                    if is_known_class
                    else
                    config.default_class
                )

                await bot.send_message(
                    chat_id = (
                        class_["channel_id"]
                        if is_known_class
                        else
                        config.default_class["channel_id"]
                    ),
                    text = TEXTS["edupage"]["timetable"]["default"].format(
                        additional_text = TEXTS["edupage"]["timetable"]["changed"],
                        daysdefs = "\n\n".join([
                            TEXTS["edupage"]["timetable"]["daysdef"].format(
                                daysdef = tables_["daysdefs"][day_id]["name"],
                                lessons = "\n".join(lessons)
                            )
                            for day_id, lessons in daysdefs_lessons__.items()
                        ]),
                        main_channel_url = config.main_channel_url,
                        post_channel_href = (
                            TEXTS["edupage"]["timetable"]["url"].format(
                                url = class_["post_channel_url"],
                                class_name = class_["name"]
                            )
                            if is_known_class and class_["channel_id"] != -1
                            else
                            config.timetable.classes[classes_by_timetable_and_id_to_name[timetable_number][class_id]]["name"]
                        )
                    ),
                    disable_web_page_preview = True
                )

                await sleep(
                    delay = config.per_notify_sleep
                )

            timetable_api.save_storage()

            tables[timetable_number] = tables_

    try:
        while True:
            await _notifier()

            save_json(
                filename = config.timetable.classes_filename,
                data = classes_timetables
            )

            await sleep(
                delay = seconds
            )

    except Exception as ex:
        await errors_handler(
            update = None,
            exception = ex
        )

        return


async def on_startup() -> bool:
    global keyboards, classes_by_timetable_and_id_to_name, class_ids, class_names

    await init_db(
        db_uri = config.db_uri,
        db_name = config.db_name
    )

    classes_by_timetable_and_id_to_name = {
        timetable_number: {}
        for timetable_number in config.timetable.numbers
    }

    for class_name, class_ in config.timetable.classes.items():
        classes_by_timetable_and_id_to_name[class_["timetable_number"]][class_["id"]] = class_name
        class_ids.append(class_["id"])

        class_names[class_["name"]] = (
            class_["timetable_number"],
            class_["id"]
        )

    try:
        await timetable_load()

    except Exception as ex:
        await errors_handler(
            update = None,
            exception = ex
        )

        return False

    config.timetable.classes = load_classes(
        classes = config.timetable.classes
    )

    keyboards = Keyboards(
        texts = TEXTS["keyboards"],
        classes = config.timetable.classes,
        per_page_limit = config.per_page_limit
    )

    return True


async def on_shutdown() -> None:
    await timetable_api.close()

    await dp.storage.close()
    await dp.storage.wait_closed()

    if bot._session:
        await bot._session.close()


async def main() -> None:
    from asyncio import gather

    startup_status_ok: bool = await on_startup()

    if not startup_status_ok:
        return

    await gather(
        notifier(
            seconds = config.notifier_seconds
        ),
        dp.start_polling()
    )


if __name__ == "__main__":
    from asyncio import AbstractEventLoop, new_event_loop, set_event_loop

    loop: AbstractEventLoop = new_event_loop()

    set_event_loop(
        loop = loop
    )

    try:
        loop.run_until_complete(
            main()
        )

    except KeyboardInterrupt:
        pass

    finally:
        loop.run_until_complete(
            on_shutdown()
        )
