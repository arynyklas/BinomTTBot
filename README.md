# Bot to take current timetable and monitor updates in channels for Binom Capital School via edupage.org's API

# Technologies used:
### [MongoDB](https://www.mongodb.com/) - 4.4.6
### [Python](https://www.python.org/) - 3.7+
### [beanie](https://pypi.org/project/beanie/) - 1.11.9
### [dictdiffer](https://pypi.org/project/dictdiffer/) - 0.9.0
### [aiohttp](https://pypi.org/project/aiohttp/) - 3.8.1

# Config setup:
- Rename `config.yml.example` to `config.yml`
- Set values for this keys: `bot_token`, `db_uri`, `db_name`, `main_channel_url`
- Set values for `admins` (it means list of Telegram users' ID, which will receive information if edupage.org will give incorrect responses)
- Set value for `channel_id` and `post_channel_url` in `default_class` (the channel to track all changes of timetables)
- If you want, you can track timetable changes into other channels:
  - Set class name as key for your class in `classes`
  - Set value for `name` (it means class name)
  - Set `id` from edupage.org
  - Set `timetable_number` from edupage.org
  - Set `channel_id` of your channel
  - Set `bot_channel_url` of your channel (it means people's source is bot)
  - Set `post_channel_url` of your channel (it means people's source is post)

# Authors:
### [Aryn](https://t.me/aryn_bots) - 15 y.o.

# License:
### [MIT](../master/LICENSE.md)
