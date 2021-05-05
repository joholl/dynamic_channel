# SPDX-License-Identifier: GPL-3.0

import logging
from typing import Generator, List

from discord import Guild, PermissionOverwrite, StageChannel, TextChannel

from dynamic_channel.control_channel import ControlChannel
from dynamic_channel.dyn_channel import DynChannel
# from dynamic_channel.log import LogChannel

logger = logging.getLogger(__name__)


class DynCategory:
    def __init__(self, dyn_guild, category, category_info):
        self.dyn_guild = dyn_guild
        self.category = category
        self.category_info = category_info

        # tracked DynChannels, created by bot and owned by user during runtime
        self._tracked_dyn_channels = []

    @property
    def client(self):
        return self.dyn_guild.client

    @property
    def guild(self) -> Guild:
        return self.dyn_guild.guild

    def control_message_text(self) -> str:
        """Get the bot control message text."""
        text = ""
        if self._tracked_dyn_channels:
            text += "```\n"
            text += "Stages\n"
            for dyn_channel in self._tracked_dyn_channels:
                text += f" - {dyn_channel}\n"
            text += "```\n"
        text += self.category_info.bot_control_message
        return text

    @property
    async def control_channel(self) -> ControlChannel:
        return ControlChannel(self, await self.control_text_channel, self.control_message_text)

    @property
    async def control_text_channel(self) -> TextChannel:
        try:
            return next(
                c
                for c in self.category.channels
                if isinstance(c, TextChannel) and c.name == self.category_info.log_channel_name
            )
        except StopIteration as e:
            logger.warning(
                f"[{self.category.guild}] Could not find any text channel in category '{self.category_info.category_name}' in guild {self.category.guild}. Creating..."
            )
            overwrites = {
                self.category.guild.me: PermissionOverwrite(send_messages=True),
                self.category.guild.default_role: PermissionOverwrite(send_messages=False),
            }
            return await self.category.create_text_channel(
                name=self.category_info.text_channel_name,
                topic=self.category_info.text_channel_topic,
                overwrites=overwrites,
            )

    # @property
    # async def log_channel(self) -> LogChannel:
    #     return LogChannel(self, await self.log_text_channel)

    @property
    async def log_text_channel(self) -> TextChannel:
        try:
            return next(
                c for c in self.category.channels if isinstance(c, TextChannel) and self.category_info.text_channel_name
            )  # TODO
        except StopIteration as e:
            logger.warning(
                f"[{self.category.guild}] Could not find any text channel in category '{self.category_info.category_name}' in guild {self.category.guild}. Creating..."
            )
            overwrites = {
                self.category.guild.me: PermissionOverwrite(send_messages=True),
                self.category.guild.default_role: PermissionOverwrite(send_messages=False),
            }
            return await self.category.create_text_channel(
                name=self.category_info.text_channel_name,
                topic=self.category_info.text_channel_topic,
                overwrites=overwrites,
            )

    # @property
    # def stage_channels(self) -> Generator[StageChannel, None, None]:
    #     return (c for c in self.category.channels if isinstance(c, StageChannel))

    @property
    def dyn_channels(self) -> List[DynChannel]:
        return self._tracked_dyn_channels

    def dyn_channel_from_owner(self, owner) -> DynChannel:
        return next(dyn_channel for dyn_channel in self._tracked_dyn_channels if dyn_channel.owner == owner)

    def dyn_channel_fom_channel(self, channel) -> DynChannel:
        if isinstance(channel, TextChannel):
            try:
                return next(
                    dyn_channel for dyn_channel in self._tracked_dyn_channels if dyn_channel.text_channel == channel
                )
            except StopIteration:
                return None

        if isinstance(channel, StageChannel):
            try:
                return next(
                    dyn_channel for dyn_channel in self._tracked_dyn_channels if dyn_channel.stage_channel == channel
                )
            except StopIteration:
                return None

    async def create_dyn_channel(self, owner):
        """Create a new stage if user does not already own one."""
        try:
            # Getting the dyn_channel will raise a StopIteration if owner does not own DynChannel
            dyn_channel = self.dyn_channel_from_owner(owner=owner)

            logger.warning(
                f"[{self.guild}] Refusing to create new stage. User {owner} already owns a dyn_channel: {dyn_channel}"
            )
            return
        except StopIteration:
            pass

        dyn_channel = DynChannel(self, owner)
        await dyn_channel.create()
        self._tracked_dyn_channels.append(dyn_channel)

    async def delete_dyn_channel(self, owner):
        """Delete the stage owned by a given owner."""
        try:
            # Getting the dyn_channel will raise a StopIteration if owner does not own DynChannel
            dyn_channel = self.dyn_channel_from_owner(owner=owner)
            await dyn_channel.destroy()
            self._tracked_dyn_channels.remove(dyn_channel)

        except StopIteration:
            logger.warning(f"[{self.guild}] User {owner} does not owns a dyn_channel. Refusing to delete.")
        except RuntimeError:
            logger.warning(f"[{self.guild}] User {owner} wants to delete their dyn_channel but it is not empty. Refusing.")

    async def delete_all_dyn_channels(self):
        for dyn_channel in self._tracked_dyn_channels:
            await dyn_channel.destroy(force=True)
        self._tracked_dyn_channels = []

    async def delete_all_untracked_channels(self):
        tracked_channels = [c for d in self.dyn_channels for c in d.channels] + [
            (await self.control_channel).text_channel
        ]
        for channel in self.category.channels:
            if channel not in tracked_channels:
                await channel.delete()
