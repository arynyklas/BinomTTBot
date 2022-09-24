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
            "url": "<a href=\"{url}\">{class_name}</a>",
        }
    },
    "start": "Привет!\nЯ даю расписания для всех классов.\nВыберите Ваш класс:",
    "keyboards": {
        "timetable_inline": "Изменения",
        "prev": "⬅️",
        "next": "➡️"
    }
}