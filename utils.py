from json import dump as dump_json, load as load_json

from typing import Union


def read_json(filename: str) -> Union[dict, list]:
    with open(filename, "r", encoding="utf-8") as file:
        return load_json(
            fp = file
        )


def save_json(filename: str, data: Union[dict, list]) -> None:
    with open(filename, "w", encoding="utf-8") as file:
        dump_json(
            obj = data,
            fp = file,
            ensure_ascii = False,
            indent = 4
        )
