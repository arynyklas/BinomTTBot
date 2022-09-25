TEXTS: dict = {
    "edupage": {
        "timetable": {
            "inline_title": "Расписание {class_name} класса",
            "bot": "Расписание \"<b>{class_name}</b>\" класса:\n\n",
            "changed": "Расписание изменено!\n\n",
            "default": "{additional_text}{daysdefs}\n\n<a href=\"{main_channel_url}\">Binom TimeTable</a> | {post_channel_href}",
            "daysdef": "{daysdef}:\n{lessons}",
            "lesson": "{period} ({start_time} - {end_time}) - {subject} ({teachers}) - {groups} - [{classrooms}]",
            "unknown_lesson": "{period} ({start_time} - {end_time}) - Ничего",
            "url": "<a href=\"{url}\">{class_name}</a>"
        }
    },
    "admins": {
        "table_rights_changed": {
            "default": "#error #timetables\nНет доступа к расписаниям.\nСписок расписаний:\n{timetables}",
            "timetable": "<code>{number}</code> - <i>{text}</i>"
        },
        "unknown_error": "#error\nНеизвестная ошибка:\n<code>{traceback}</code>\n\n<code>{update}</code>"
    },
    "start": "Привет!\nЯ даю расписания для всех классов.\nВыберите Ваш класс:",
    "keyboards": {
        "timetable_inline": "Изменения",
        "prev": "⬅️",
        "next": "➡️"
    },
    "alphabet": [
        "А",
        "Ә",
        "Б",
        "В",
        "Г",
        "Ғ",
        "Д",
        "Е",
        "Ё",
        "Ж",
        "З",
        "И",
        "Й",
        "К",
        "Қ",
        "Л",
        "М",
        "Н",
        "Ң",
        "О",
        "Ө",
        "П",
        "Р",
        "С",
        "Т",
        "У",
        "Ұ",
        "Ү",
        "Ф",
        "Х",
        "Һ",
        "Ц",
        "Ч",
        "Ш",
        "Щ",
        "Ъ",
        "Ы",
        "І",
        "Ь",
        "Э",
        "Ю",
        "Я"
    ]
}