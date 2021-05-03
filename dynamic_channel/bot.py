# SPDX-License-Identifier: GPL-3.0
import asyncio
import datetime
import logging
from typing import Dict, Generator, List

from discord import (
    Client,
    Guild,
    PermissionOverwrite,
    StageChannel,
    TextChannel,
)

from dynamic_channel.guild import DynChannelGuild
from dynamic_channel.message import ReactMessage, react_to

logger = logging.getLogger(__name__)


class CategoryInfo:
    def __init__(
        self,
        category_name,
        text_channel_name,
        text_channel_topic,
        bot_control_message,
        log_channel_name,
        stage_max_minutes,
    ):
        self.category_name = category_name
        self.text_channel_name = text_channel_name
        self.text_channel_topic = text_channel_topic
        self.bot_control_message = bot_control_message
        self.log_channel_name = log_channel_name
        self.stage_max_minutes = stage_max_minutes


class DynChannelBot(Client):
    def __init__(self, category_info):
        super().__init__()
        self.category_info = category_info  # TODO is there a better way to do this? either way: typing

        self._dyn_channel_guilds: Dict[Guild, DynChannelGuild] = {}

        # start timer function, will be called periodically
        # TODO
        # loop = asyncio.get_event_loop()
        # loop.create_task(self.periodic())

    async def dyn_channel_guild(self, guild: Guild) -> DynChannelGuild:
        if guild in self._dyn_channel_guilds:
            return self._dyn_channel_guilds[guild]

        dyn_guild = DynChannelGuild(client=self, guild=guild, category_info=self.category_info)
        self._dyn_channel_guilds[guild] = dyn_guild
        return dyn_guild

    async def periodic(self):
        while True:
            await asyncio.sleep(30)

            logger.info(f"Perform periodic actions.")
            for guild in self.guilds:
                dyn_guild = await self.dyn_channel_guild(guild=guild)
                dyn_category = await dyn_guild.dyn_channel_category
                await dyn_category.delete_old_stages()  # TODO implement delete

                # TODO update message?
                # control_channel = await category.control_channel
                # await self.update_control_message(channel=control_channel)

    async def on_ready(self):
        """Callback function. Is called after a successful login."""

        for guild in self.guilds:
            logger.info(f"[{guild}] Logged on as {self.user}")

            dyn_guild = await self.dyn_channel_guild(guild=guild)
            dyn_category = await dyn_guild.dyn_channel_category
            control_channel = await dyn_category.control_channel

            # request bot control message to create it if it does not exist
            await control_channel.control_message

    async def on_guild_channel_update(self, before, after):
        """Callback function. Is called once a channel is edited."""
        dyn_guild = await self.dyn_channel_guild(guild=before.guild)
        dyn_category = await dyn_guild.dyn_channel_category

        if before.name != after.name:
            dyn_channel = dyn_category.dyn_channel_fom_channel(before)
            if dyn_channel is not None:
                is_name_improper = after.name not in [dyn_channel.stage_name, dyn_channel.text_name]
                if is_name_improper:
                    logger.warning(f'Channel name was changed: "{before}" -> "{after}". Undoing the change.')
                    await after.edit(name=before.name)

    async def create_dyn_channel(self, user, control_channel):
        """Create new dynamic channel."""
        await control_channel.dyn_category.create_dyn_channel(user)

    async def delete_dyn_channel(self, user, control_channel):
        """Delete a dynamic channels."""
        await control_channel.dyn_category.delete_dyn_channel(user)

    async def delete_all_channels(self, user, control_channel):
        """Delete all dynamic channels, including the untracked ones."""
        if not user.guild_permissions.manage_channels:
            logger.warning(
                f"[{control_channel.guild}] Refusing to delete all stages. User {user} does not have manage_channels permission."
            )
            return

        logger.warning(f"[{control_channel.guild}] {user} purges all stages. Burn them alive!")

        # delete tracked channels
        await control_channel.dyn_category.delete_all_dyn_channels()

        # delete untracked channels
        await control_channel.dyn_category.delete_all_untracked_channels()

    # async def on_message(self, message):
    #     """Callback function. Is called after the bot registers a message."""
    #     # find (or create) stages category in guild
    #     category = await DeviantGuild(message.guild).category
    #
    #     # to any message in stages category, add bot control message below
    #     if message.channel.category == category and message.author != self.user:
    #         logger.info(f"[{message.guild}] Message from {message.author}: {message.content}")
    #         await self.update_control_message(message.channel)
