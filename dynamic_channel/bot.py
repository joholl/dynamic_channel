# SPDX-License-Identifier: GPL-3.0
import asyncio
import datetime
import logging
from typing import Generator

from discord import Client, Guild, PermissionOverwrite, StageChannel, TextChannel

from dynamic_channel.message import ReactMessage, react_to

logger = logging.getLogger(__name__)


class ControlMessage(ReactMessage):
    def __init__(self, client, text):
        super().__init__(text)
        self.client = client

    async def update_text(self):
        """Update message text."""
        await self.set_text(self.client.control_message_text(self.message.channel))

    @react_to("🆕", remove=True)
    async def new_stage(self, reaction, user):
        await self.client.create_stage(user, self.message.channel.category)
        await self.update_text()

    @react_to("❌", remove=True)
    async def delete_stage(self, reaction, user):
        await self.client.delete_stage(owner=user, guild=reaction.message.guild)
        await asyncio.sleep(0.1)
        await self.update_text()

    # @react_to("🗑️️️", remove=True)
    @react_to("🔥", remove=True)
    async def delete_all_stages(self, reaction, user):
        if not user.guild_permissions.manage_channels:
            logger.warning(
                f"[{reaction.message.guild}] Refusing to delete all stages. User {user} does not have manage_channels permission."
            )
            return
        await self.client.delete_all_stages(self.message.channel.category)
        await asyncio.sleep(0.1)
        await self.update_text()

    # @react_to("🔄", remove=True)
    # async def reload(self, reaction, user):
    #     await self.update_text()


class CategoryInfo:
    def __init__(
        self,
        category_name,
        text_channel_name,
        text_channel_topic,
        bot_control_message,
        stage_max_minutes,
    ):
        self.category_name = category_name
        self.text_channel_name = text_channel_name
        self.text_channel_topic = text_channel_topic
        self.bot_control_message = bot_control_message
        self.stage_max_minutes = stage_max_minutes


class StageCategory:
    def __init__(self, category, category_info):
        self.category = category
        self.category_info = category_info

    @property
    def guild(self) -> Guild:
        return self.category.guild

    @property
    async def text_channel(self) -> TextChannel:
        try:
            return next(c for c in self.category.channels if isinstance(c, TextChannel))
        except StopIteration as e:
            logger.warning(
                f"[{self.category.guild}] Could not find any text channel in category '{self.category_info.CATEGORY_NAME}' in guild {self.category.guild}. Creating..."
            )
            overwrites = {
                self.category.guild.me: PermissionOverwrite(send_messages=True),
                self.category.guild.default_role: PermissionOverwrite(
                    send_messages=False
                ),
            }
            return await self.category.create_text_channel(
                name=self.category_info.text_channel_name,
                topic=self.category_info.text_channel_topic,
                overwrites=overwrites,
            )

    @property
    def stage_channels(self) -> Generator[StageChannel, None, None]:
        return (c for c in self.category.channels if isinstance(c, StageChannel))


class DynChannelGuild:
    def __init__(self, guild, category_info):
        self.guild = guild
        self.category_info = category_info

    @property
    async def category(self) -> StageCategory:
        try:
            category = next(
                c
                for c in self.guild.categories
                if c.name == self.category_info.category_name
            )
        except StopIteration as e:
            logger.warning(
                f"[{self.guild}] Could not find category '{self.category_info.category_name}' in guild {self.guild}. Creating..."
            )
            category = await self.guild.create_category(
                self.category_info.category_name
            )
        return StageCategory(category, self.category_info)


class DynChannelClient(Client):  # TODO
    def __init__(self, category_info):
        super().__init__()
        self.category_info = category_info

        # tracked stages, keyed by guild, then keyed by owner (created by bot and owned by user during runtime)
        self._stages = {}

        # control messages, keyed by guild
        self._control_messages = {}

        # start timer function, will be called periodically
        loop = asyncio.get_event_loop()
        loop.create_task(self.periodic())

    async def periodic(self):
        while True:
            await asyncio.sleep(30)

            logger.debug(f"Perform periodic actions.")
            for guild in self.guilds:
                category = await DynChannelGuild(guild, self.category_info).category
                await self.delete_old_stages(category)

                # TODO after updating the message, reactions (and therefore edit()) will result in Unknown Message
                text_channel = await category.text_channel
                await self.update_control_message(channel=text_channel)

    def control_message_text(self, channel) -> str:
        """Get the bot control message text."""
        text = ""
        stage_channels = [
            c for c in channel.category.channels if isinstance(c, StageChannel)
        ]  # TODO use class
        if stage_channels:
            text += "```\n"
            text += "Stages\n"
            for stage in stage_channels:
                line = f"  {stage.name}"
                if stage.topic:
                    line += f': "{stage.topic}"'
                if stage not in self._stages[channel.guild].values():
                    line = line.ljust(50) + " [untracked]"
                text += f"{line}\n"
            text += "```\n"
        text += self.category_info.bot_control_message
        return text

    async def update_control_message(self, channel):
        """Update the bot control message."""
        control_message = self._control_messages[channel.guild]
        logger.debug(
            f"[{channel.guild}] Update bot control message: {control_message.message}"
        )
        await control_message.update_text()

    # TODO use update_control_message, i.e. use existing msg if there, create otherwise. in beginning delete every own msg that is not the latest
    async def reset_text_channel(self, channel):
        """Delete all prior control messages in the given channel and create new one."""

        # delete all prior messages in the same text channel (except the last one if it is by the bot)
        async for message in channel.history().filter(
            lambda msg: msg.author == self.user
        ):
            logger.debug(
                f"[{channel.guild}] Deleting prior bot control message: {message}"
            )
            await message.delete()

        # post new bot control message
        text = self.control_message_text(channel)
        logger.debug(
            f"[{channel.guild}] Posting new bot control message in channel {channel}: {text}"
        )

        self._control_messages[channel.guild] = ControlMessage(self, text=text)
        loop = asyncio.get_event_loop()
        loop.create_task(self._control_messages[channel.guild].send_and_wait(channel))

    async def create_stage(self, owner, category):
        """Create a new stage if user does not already own one."""
        if owner in self._stages[category.guild]:
            logger.warning(
                f"[{category.guild}] Refusing to create new stage. User {owner} already owns a stage: {self._stages[category.guild][owner]}"
            )
            return

        logger.debug(f"[{category.guild}] Creating new stage for user {owner}.")
        stage_name = f" - {owner.display_name}'s stage"
        overwrites = {
            owner: PermissionOverwrite(
                request_to_speak=True,
                manage_channels=True,
                move_members=True,
                mute_members=True,
            ),
        }
        stage_channel = await category.guild.create_stage_channel(
            name=stage_name, category=category, overwrites=overwrites
        )

        self._stages[category.guild][owner] = stage_channel

    async def _delete_stage(
        self, stage=None, owner=None, guild=None
    ):  # TODO and nobody in present in stage
        """Delete stage by stage or owner. If owner was given, guild must be given, too. Does not raise exceptions."""
        if stage is None and owner is None:
            raise ValueError("stage and owner cannot be None at the same time.")
        if stage is not None and owner is not None:
            raise ValueError("stage and owner cannot be set at the same time.")
        if owner is not None and guild is None:
            raise ValueError("if owner is given, guild has to be given, too.")

        if stage is not None:
            # stage was given, look up owner in tracked stages
            try:
                owner = next(
                    k for k, v in self._stages[stage.guild].items() if v == stage
                )
            except StopIteration:
                # could not find stage in list of tracked stages, delete anyway
                pass
            guild = stage.guild
        else:
            # owner was given, look up owner in tracked stages
            try:
                stage = self._stages[guild][owner]
            except KeyError:
                logger.warning(
                    f"[{guild}] Could not delete stage owned by {owner}. Does not own any."
                )
                return

        if owner is not None:
            # delete from tracked stages
            del self._stages[guild][owner]

        logger.debug(f"[{guild}] Deleting stage owned by {owner}: {stage}")
        await stage.delete()

    async def delete_all_stages(self, category):
        """Delete all stage channels in category."""
        for channel in category.channels:
            if isinstance(channel, StageChannel):
                await self._delete_stage(stage=channel)

    async def delete_stage(self, owner, guild):
        """Delete stage channel owned by a given user."""
        await self._delete_stage(owner=owner, guild=guild)

    async def delete_old_stages(self, category):
        """Delete all old stages."""
        for stage in category.stage_channels:
            if (
                datetime.datetime.utcnow()
                - datetime.timedelta(minutes=self.category_info.stage_max_minutes)
                > stage.created_at
            ):
                logger.debug(f"[{category.guild}] Delete old stage: {stage}")
                await self._delete_stage(stage=stage)

    async def delete_untracked_stages(self):
        """Delete all untracked stages. Untracked stages existed prior to bot login."""
        # TODO implement and maybe call this at login (for all guilds)? maybe also periodically?

    async def on_ready(self):
        """Callback function. Is called after a successful login."""

        # leave a control message in the first properly named category (which might be created)
        for guild in self.guilds:
            logger.debug(f"[{guild}] Logged on as {self.user}")
            self._stages[guild] = {}

            category = await DynChannelGuild(guild, self.category_info).category
            text_channel = await category.text_channel
            await self.reset_text_channel(text_channel)

    # async def on_message(self, message):
    #     """Callback function. Is called after the bot registers a message."""
    #     # find (or create) stages category in guild
    #     category = await DeviantGuild(message.guild).category
    #
    #     # to any message in stages category, add bot control message below
    #     if message.channel.category == category and message.author != self.user:
    #         logger.debug(f"[{message.guild}] Message from {message.author}: {message.content}")
    #         await self.update_control_message(message.channel)
