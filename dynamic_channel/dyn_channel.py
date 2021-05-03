# SPDX-License-Identifier: GPL-3.0

import logging

from discord import (
    CategoryChannel,
    Guild,
    Member,
    PermissionOverwrite,
    StageChannel,
    TextChannel,
)

logger = logging.getLogger(__name__)


class DynChannel:
    def __init__(self, dyn_category, owner):
        self.dyn_category = dyn_category
        self.owner: Member = owner

        self.text_channel: TextChannel = None
        self.stage_channel: StageChannel = None

    @property
    def client(self):
        return self.dyn_category.client

    @property
    def guild(self) -> Guild:
        return self.dyn_category.guild

    @property
    def category(self) -> CategoryChannel:
        return self.dyn_category.category

    @property
    def stage_name(self):
        return f"{self.owner.display_name}'s stage"

    @property
    def text_name(self):
        return f"{self.owner.display_name}'s text"

    @property
    def channels(self):
        return [self.stage_channel, self.text_channel]

    async def create(self):
        logger.info(f"[{self.guild}] Creating new stage for user {self.owner}.")
        overwrites = {
            self.owner: PermissionOverwrite(
                request_to_speak=True,
                manage_channels=True,
                move_members=True,
                mute_members=True,
            ),
        }
        self.stage_channel = await self.guild.create_stage_channel(
            name=self.stage_name, category=self.category, overwrites=overwrites
        )
        self.text_channel = await self.guild.create_text_channel(name=self.text_name, category=self.category)

    async def destroy(self, force=False):  # TODO and nobody in present in stage
        """Delete text and stage."""
        if self.stage_channel.members and not force:
            logger.warning(
                f"[{self.guild}] Refusing to delete stage {self.stage_channel.name} because there are members in it: {self.owner}"
            )
            return

        logger.info(f"[{self.guild}] Deleting text channel owned by {self.owner}: {self.text_channel}")
        await self.text_channel.delete()

        logger.info(f"[{self.guild}] Deleting stage channel owned by {self.owner}: {self.stage_channel}")
        await self.stage_channel.delete()

    def __str__(self):
        string = f"{self.stage_name}"
        if self.stage_channel.topic:
            string += f': "{self.stage_channel.topic}"'
        return string
