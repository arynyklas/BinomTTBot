from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from itertools import islice

from typing import Iterator, Dict, Callable, List, Union


def chunks(data: dict, size: int):
    data_iter: Iterator = iter(data)

    for _ in range(0, len(data), size):
        yield {
            k: data[k]
            for k in islice(data_iter, size)
        }


class Keyboards:
    def __init__(self, texts: dict, classes: Dict[str, Dict[str, Union[str, int]]], per_page_limit: int) -> None:
        self._texts: dict = texts
        self._per_page_limit: int = per_page_limit

        self._classes: List[Dict[str, Dict[str, Union[str, int]]]] = list(chunks(
            data = classes,
            size = per_page_limit
        ))

        self._max_classes_page: int = len(self._classes) - 1

    def get_classes(self, page: int) -> None:
        markup: InlineKeyboardMarkup = InlineKeyboardMarkup(
            row_width = 2
        )

        for i, class_name in enumerate(self._classes[page].keys(), 0):
            i: int
            class_name: str

            class_: dict = self._classes[page][class_name]

            func: Callable

            if i % self._per_page_limit == 0 or i % 2 == 0:
                func = markup.add
            else:
                func = markup.insert

            func(
                InlineKeyboardButton(
                    text = class_name,
                    callback_data = "timetable_class_{class_id}_{timetable_number}".format(
                        class_id = class_["id"],
                        timetable_number = class_["timetable_number"]
                    )
                )
            )

        have_prev: bool = page > 0

        if have_prev:
            markup.add(
                InlineKeyboardButton(
                    text = self._texts["prev"],
                    callback_data = "timetable_page_{page}".format(
                        page = page - 1
                    )
                )
            )

        if self._max_classes_page > page:
            if have_prev:
                func = markup.insert
            else:
                func = markup.add

            func(
                InlineKeyboardButton(
                    text = self._texts["next"],
                    callback_data = "timetable_page_{page}".format(
                        page = page + 1
                    )
                )
            )

        return markup

    def inline_timetable(self, channel_url: str) -> str:
        return InlineKeyboardMarkup(
            inline_keyboard = [[
                InlineKeyboardButton(
                    text = self._texts["timetable_inline"],
                    url = channel_url
                )
            ]]
        )
