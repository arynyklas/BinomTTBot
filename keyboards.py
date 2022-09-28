from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from itertools import islice

from typing import Any, Iterator, Dict, Callable, List, Union


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

        self._max_classes_page: int

        self.classes: List[InlineKeyboardMarkup]

        self.update_classes(
            classes = classes
        )

    def update_classes(self, classes: Dict[str, Dict[str, Union[str, int]]]) -> None:
        self.classes = []

        _classes: List[Any] = list(chunks(
            data = classes,
            size = self._per_page_limit
        ))

        self._max_classes_page = len(_classes) - 1

        for page in range(len(_classes)):
            page: int

            class_markup: InlineKeyboardMarkup = InlineKeyboardMarkup(
                row_width = 2
            )

            for class_name, class_ in _classes[page].items():
                class_name: str

                class_markup.insert(
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
                class_markup.add(
                    InlineKeyboardButton(
                        text = self._texts["prev"],
                        callback_data = "timetable_page_{page}".format(
                            page = page - 1
                        )
                    )
                )

            if self._max_classes_page > page:
                if have_prev:
                    func = class_markup.insert
                else:
                    func = class_markup.add

                func(
                    InlineKeyboardButton(
                        text = self._texts["next"],
                        callback_data = "timetable_page_{page}".format(
                            page = page + 1
                        )
                    )
                )

            self.classes.append(class_markup)

    def inline_timetable(self, channel_url: str) -> str:
        return InlineKeyboardMarkup(
            inline_keyboard = [[
                InlineKeyboardButton(
                    text = self._texts["timetable_inline"],
                    url = channel_url
                )
            ]]
        )
