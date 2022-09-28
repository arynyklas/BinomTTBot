from dataclasses import dataclass, asdict
from yaml import load as load_yaml, Loader, dump as dump_yaml

from typing import Dict, List, Union


@dataclass
class TimetableConfig:
    storage_filename: str
    response_filename: str
    classes_filename: str
    numbers: List[str]
    old_numbers: Dict[str, str]
    classes: Dict[str, Dict[str, Union[str, int]]]


@dataclass
class Config:
    bot_token: str
    db_uri: str
    db_name: str
    main_channel_url: str
    notifier_seconds: int
    per_page_limit: int
    per_notify_sleep: float
    inline_cache_time: int
    admins: List[int]
    clear_class: dict
    default_class: dict
    timetable: TimetableConfig


config_filename: str = "config.yml"


with open(config_filename, "r", encoding="utf-8") as file:
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


def save_config(config: Config) -> None:
    with open(config_filename, "w", encoding="utf-8") as file:
        dump_yaml(
            data = asdict(config),
            allow_unicode = True,
            indent = 2
        )


__all__ = (
    "config_filename",
    "config",
    "save_config",
)
