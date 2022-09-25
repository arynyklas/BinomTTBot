from aiohttp import ClientSession, TCPConnector, ClientResponse, hdrs
from json import loads as loads_json

from utils import read_json, save_json

from dataclasses import dataclass
from pytz import timezone
from pytz.tzinfo import DstTzInfo
from hashlib import md5
from datetime import datetime
from dictdiffer import diff as diff_checker
from copy import deepcopy

from typing import Dict, List, Optional, Tuple, Union


tables_list: List[str] = [
    "teachers",
    "subjects",
    "classes",
    "groups",
    "classrooms",
    "lessons",
    "cards",
    "periods",
    "daysdefs"
]


@dataclass
class Lesson:
    card_id: str
    lesson_id: str
    subjectid: str
    teacherids: List[str]
    groupids: List[str]
    durationperiods: int
    classroomidss: List[List[str]]
    day_id: str
    period: str


@dataclass
class TimeTableInfo:
    number: str
    text: str


class TimeTable:
    API_URL: str = "https://binomcapital.edupage.org{path}"

    INCORRECT_PERIODS: List[str] = [
        "",
        "-1"
    ]

    TZ: DstTzInfo = timezone(
        zone = "Asia/Almaty"
    )

    def __init__(self, storage_path: str, response_path: str) -> None:
        self.storage_path: str = storage_path
        self.response_path: str = response_path

        self.storage: Dict[str, Dict[str, str]]

        try:
            self.storage = read_json(
                filename = self.storage_path
            )

        except:
            self.storage = {}

            save_json(
                filename = self.storage_path,
                data = self.storage
            )

        self.storage.setdefault(
            "latest_hash",
            None
        )

    def save_storage(self) -> None:
        save_json(
            filename = self.storage_path,
            data = self.storage
        )

    def table_to_dict(self, table_rows: List[dict]) -> Dict[str, dict]:
        result: Dict[str, dict] = {}

        for table_row in table_rows:
            table_row: dict

            result[table_row["id"]] = table_row

        return result

    def load_tables(self, tables: List[dict]) -> Dict[str, Dict[str, dict]]:
        results: Dict[str, Dict[str, dict]] = {}

        for table_data in tables:
            table_id: str = table_data["id"]

            if table_id in tables_list:
                results[table_id] = self.table_to_dict(
                    table_rows = table_data["data_rows"]
                )

        return results

    async def request(self, url: str, method: str, **kwargs) -> str:
        session: ClientSession = getattr(
            self,
            "_session",
            None
        )

        if not session:
            session = ClientSession(
                connector = TCPConnector(
                    limit = None,
                    ttl_dns_cache = 300
                )
            )

            setattr(
                self,
                "_session",
                session
            )

        response_text: str

        async with session.request(
            method = method,
            url = url,
            **kwargs
        ) as response:
            response: ClientResponse

            response_text: str = await response.text(
                encoding = "utf-8"
            )

        return response_text

    async def _get_timetables(self, timetable_number: str) -> str:
        return await self.request(
            url = self.API_URL.format(
                path = "/timetable/server/regulartt.js"
            ),
            method = hdrs.METH_POST,
            params = {
                "__func": "regularttGetData"
            },
            json = {
                "__args": [
                    None,
                    timetable_number
                ],
                "__gsh": "00000000"
            }
        )

    async def get_active_timetables_info(self) -> List[TimeTableInfo]:
        response_text: str = await self.request(
            url = self.API_URL.format(
                path = "/timetable/server/ttviewer.js"
            ),
            method = hdrs.METH_POST,
            params = {
                "__func": "getTTViewerData"
            },
            json = {
                "__args": [
                    None,
                    str(datetime.now(
                        tz = self.TZ
                    ).year)
                ],
                "__gsh": "00000000"
            }
        )

        response_json: dict = loads_json(
            s = response_text
        )["r"]["regular"]["timetables"]

        results: List[TimeTableInfo] = []

        for timetable in response_json:
            timetable: dict

            if not timetable["hidden"]:
                results.append(
                    TimeTableInfo(
                        number = timetable["tt_num"],
                        text = timetable["text"]
                    )
                )

        return results

    async def get_timetables(self, timetable_number: str, class_ids: Optional[List[str]]=None) -> Tuple[Dict[str, Dict[str, Dict[str, Lesson]]], Dict[str, Dict[str, dict]]]:
        response_text: str = await self._get_timetables(
            timetable_number = timetable_number
        )

        calculated_hash: str = md5(
            string = response_text.encode("utf-8")
        ).hexdigest()

        if calculated_hash == self.storage["latest_hash"]:
            return {}, {}
        else:
            self.storage["latest_hash"] = calculated_hash

        response_json: dict = loads_json(
            s = response_text
        )

        save_json(
            filename = self.response_path.format(
                number = timetable_number
            ),
            data = response_json
        )

        response_json: List[dict] = response_json["r"]["dbiAccessorRes"]["tables"]

        tables: Dict[str, Dict[str, dict]] = self.load_tables(
            tables = response_json
        )

        val_id_daysdefs: Dict[str, str] = {}
        DEFAULT_DAY_LESSONS: Dict[str, Dict[str, Union[str, int]]] = {}

        for daysdef_id, daysdef in tables["daysdefs"].items():
            if daysdef["val"] == None:
                continue

            val_id_daysdefs[daysdef["vals"][0]] = daysdef_id
            DEFAULT_DAY_LESSONS[daysdef_id] = {}

        results: Dict[str, Dict[str, Dict[str, Dict[str, str]]]] = {}

        for card in tables["cards"].values():
            lesson: dict = tables["lessons"][card["lessonid"]]
            class_id: str = lesson["classids"][0]

            if class_ids:
                if class_id not in class_ids:
                    continue

            if card["period"] in self.INCORRECT_PERIODS:
                continue

            day_id: str = val_id_daysdefs[card["days"]]
            period_start = tables["periods"][card["period"]]

            if class_id not in results:
                results[class_id] = deepcopy(DEFAULT_DAY_LESSONS)

            results[class_id][day_id][period_start["period"]] = Lesson(
                card_id = card["id"],
                lesson_id = lesson["id"],
                subjectid = lesson["subjectid"],
                teacherids = lesson["teacherids"],
                groupids = lesson["groupids"],
                durationperiods = lesson["durationperiods"],
                classroomidss = card["classroomids"],
                day_id = day_id,
                period = card["period"]
            )

        return results, tables

    async def get_newest_timetables(self, timetable_number: str, old_tables: Dict[str, Dict[str, dict]]) -> Tuple[Dict[str, Dict[str, Dict[str, Lesson]]], Dict[str, Dict[str, dict]]]:
        response_text: str = await self._get_timetables(
            timetable_number = timetable_number
        )

        calculated_hash: str = md5(
            string = response_text.encode("utf-8")
        ).hexdigest()

        if calculated_hash == self.storage["latest_hash"]:
            return {}, {}
        else:
            self.storage["latest_hash"] = calculated_hash

        response_json: dict = loads_json(
            s = response_text
        )

        save_json(
            filename = self.response_path.format(
                number = timetable_number
            ),
            data = response_json
        )

        response_json: List[dict] = response_json["r"]["dbiAccessorRes"]["tables"]

        tables: Dict[str, Dict[str, dict]] = self.load_tables(
            tables = response_json
        )

        val_id_daysdefs: Dict[str, str] = {}
        DEFAULT_DAY_LESSONS: Dict[str, Dict[str, Union[str, int]]] = {}

        for daysdef_id, daysdef in tables["daysdefs"].items():
            if daysdef["val"] == None:
                continue

            val_id_daysdefs[daysdef["vals"][0]] = daysdef_id
            DEFAULT_DAY_LESSONS[daysdef_id] = {}

        table_id: str = "cards"

        card_ids: List[str] = []

        for d in diff_checker(old_tables[table_id], tables[table_id]):
            d_type: str = d[0]
            card_id: str

            if d_type == "add":
                card_id = d[2][0][0]
            elif d_type == "change":
                card_id = (d[1] if isinstance(d[1], str) else d[1][0]).split(".", 1)[0]
            elif d_type == "remove":
                card_id = d[2][0][0]

            card_ids.append(card_id)

        results: Dict[str, Dict[str, Dict[str, Dict[str, Dict[str, str]]]]] = {}

        for card_id in card_ids:
            card: dict = tables["cards"][card_id]
            card_id: str = card["id"]

            lesson: dict = tables["lessons"][card["lessonid"]]
            class_id: str = lesson["classids"][0]

            if card["period"] in self.INCORRECT_PERIODS:
                continue

            day_id: str = val_id_daysdefs[card["days"]]
            period_start = tables["periods"][card["period"]]

            if class_id not in results:
                results[class_id] = {}

            if day_id not in results[class_id]:
                results[class_id] = deepcopy(DEFAULT_DAY_LESSONS)

            results[class_id][day_id][period_start["period"]] = Lesson(
                card_id = card["id"],
                lesson_id = lesson["id"],
                subjectid = lesson["subjectid"],
                teacherids = lesson["teacherids"],
                groupids = lesson["groupids"],
                durationperiods = lesson["durationperiods"],
                classroomidss = card["classroomids"],
                day_id = day_id,
                period = card["period"]
            )

        return results, tables

    def sort(self, class_timetable: Dict[str, Dict[str, Lesson]], not_lesson: Optional[bool]=False) -> Dict[str, Dict[str, Lesson]]:
        for key in class_timetable.keys():
            key: dict

            if not_lesson:
                class_timetable[key] = dict(sorted(class_timetable[key].items(), key=lambda kv: int(kv[0]) if kv[0][0] != "*" else int(kv[0][1:])))
            else:
                class_timetable[key] = dict(sorted(class_timetable[key].items(), key=lambda kv: int(kv[1].period) if kv[1] else 0))

        return dict(sorted(class_timetable.items(), key=lambda kv: int(kv[0]) if kv[0][0] != "*" else int(kv[0][1:])))

    async def close(self) -> None:
        session: ClientSession = getattr(
            self,
            "_session",
            None
        )

        if session:
            await session.close()
