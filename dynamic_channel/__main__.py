#!/usr/bin/env python
# SPDX-License-Identifier: GPL-3.0

import argparse
import logging
import os

from dotenv import load_dotenv

# TODO linters, README, licence, git, CI, CD?
# from dynamic_channel.log import TextChannelHandler

from .bot import CategoryInfo, DynChannelBot

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog=f"python -m {__package__}",
        description=f"Run the {__package__} discord bot.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--env", "-e", default=".env", help="environment file")
    parser.add_argument("--token", "-t", help="discord bot token (overrides .env file variable)")
    parser.add_argument(
        "--loglevel",
        "-l",
        default="INFO",
        help="logging level",
        choices=logging._nameToLevel.keys(),
    )
    parser.add_argument("--logfile", "-f", default="discord.log", help="log file path")
    args = parser.parse_args()

    root_logger = logging.getLogger()
    root_logger.setLevel(logging._nameToLevel[args.loglevel])

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # TODO
    # handler = TextChannelHandler()
    # handler.setFormatter(logging.Formatter("%(levelname)s _%(name)s_  %(message)s"))
    # handler.setLevel(logging.INFO)
    # root_logger.addHandler(handler)

    handler = logging.FileHandler(filename=args.logfile, encoding="utf-8", mode="w")
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    load_dotenv()
    TOKEN = args.token or os.getenv("DISCORD_TOKEN")
    CATEGORY_NAME = os.getenv("CATEGORY_NAME")
    TEXT_CHANNEL_NAME = os.getenv("TEXT_CHANNEL_NAME")
    TEXT_CHANNEL_TOPIC = os.getenv("TEXT_CHANNEL_TOPIC")
    STAGE_MAX_MINUTES = int(os.getenv("STAGE_MAX_MINUTES"))
    BOT_CONTROL_MESSAGE = os.getenv("BOT_CONTROL_MESSAGE")
    LOG_CHANNEL_NAME = os.getenv("LOG_CHANNEL_NAME")

    category_info = CategoryInfo(
        category_name=CATEGORY_NAME,
        text_channel_name=TEXT_CHANNEL_NAME,
        text_channel_topic=TEXT_CHANNEL_TOPIC,
        bot_control_message=BOT_CONTROL_MESSAGE,
        log_channel_name=LOG_CHANNEL_NAME,
        stage_max_minutes=STAGE_MAX_MINUTES,
    )

    logger.info("Connecting to discord.com...")
    DynChannelBot(category_info).run(TOKEN)
