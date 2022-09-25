from dataclasses import dataclass
from yaml import load as load_yaml, Loader

from typing import Dict, List, Union


@dataclass
class TimetableConfig:
    storage_filename: str
    response_filename: str
    classes_filename: str
    numbers: List[str]
    classes: Dict[str, Dict[str, Union[str, int]]]


@dataclass
class Config:
    bot_token: str
    notifier_seconds: int
    per_page_limit: int
    db_uri: str
    db_name: str
    main_channel_url: str
    inline_cache_time: int
    admins: List[int]
    clear_class: dict
    default_class: dict
    timetable: TimetableConfig


with open("config.yml", "r", encoding="utf-8") as file:
    data: dict = load_yaml(
        stream = file,
        Loader = Loader
    )

timetable: TimetableConfig = TimetableConfig(
    **data.pop("timetable")
)

config: Config = Config(
    timetable = timetable,
    **data
)


__all__ = (
    "config",
)
