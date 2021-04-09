#!/usr/bin/env python
# SPDX-License-Identifier: GPL-3.0

import logging
import os

from dotenv import load_dotenv

# TODO linters, README, licence, git, CI, CD?
from .bot import CategoryInfo, DynChannelClient

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.NOTSET)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    load_dotenv()
    TOKEN = os.getenv("DISCORD_TOKEN")
    CATEGORY_NAME = os.getenv("CATEGORY_NAME")
    TEXT_CHANNEL_NAME = os.getenv("TEXT_CHANNEL_NAME")
    TEXT_CHANNEL_TOPIC = os.getenv("TEXT_CHANNEL_TOPIC")
    STAGE_MAX_MINUTES = int(os.getenv("STAGE_MAX_MINUTES"))
    BOT_CONTROL_MESSAGE = os.getenv("BOT_CONTROL_MESSAGE")

    category_info = CategoryInfo(
        category_name=CATEGORY_NAME,
        text_channel_name=TEXT_CHANNEL_NAME,
        text_channel_topic=TEXT_CHANNEL_TOPIC,
        bot_control_message=BOT_CONTROL_MESSAGE,
        stage_max_minutes=STAGE_MAX_MINUTES,
    )

    logger.debug("Connecting to discord.com...")
    DynChannelClient(category_info).run(TOKEN)
