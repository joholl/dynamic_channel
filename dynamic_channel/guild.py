# SPDX-License-Identifier: GPL-3.0

import logging
from datetime import datetime

from discord import PermissionOverwrite, StageChannel

from dynamic_channel.category import DynCategory
from dynamic_channel.dyn_channel import DynChannel

logger = logging.getLogger(__name__)


class DynChannelGuild:
    def __init__(self, client, guild, category_info):
        self.category_info = category_info
        self.dyn_category = None
        self.client = client
        self.guild = guild

    def tracked_dyn_channel(self, owner):
        return None  # TODO

    @property
    async def dyn_channel_category(self) -> DynCategory:
        if self.dyn_category is not None:
            return self.dyn_category

        try:
            category = next(c for c in self.guild.categories if c.name == self.category_info.category_name)
        except StopIteration as e:
            logger.warning(
                f"[{self.guild}] Could not find category '{self.category_info.category_name}' in guild {self.guild}. Creating..."
            )
            category = await self.guild.create_category(self.category_info.category_name)
        self.dyn_category = DynCategory(self, category, self.category_info)
        return self.dyn_category

    # async def _delete_stage(
    #     self, stage=None, owner=None, guild=None
    # ):  # TODO and nobody in present in stage
    #     """Delete stage by stage or owner. If owner was given, guild must be given, too. Does not raise exceptions."""
    #     if stage is None and owner is None:
    #         raise ValueError("stage and owner cannot be None at the same time.")
    #     if stage is not None and owner is not None:
    #         raise ValueError("stage and owner cannot be set at the same time.")
    #     if owner is not None and guild is None:
    #         raise ValueError("if owner is given, guild has to be given, too.")
    #
    #     if stage is not None:
    #         # stage was given, look up owner in tracked stages
    #         try:
    #             owner = next(
    #                 k
    #                 for k, v in self._tracked_dyn_channels[stage.guild].items()
    #                 if v == stage
    #             )
    #         except StopIteration:
    #             # could not find stage in list of tracked stages, delete anyway
    #             pass
    #         guild = stage.guild
    #     else:
    #         # owner was given, look up owner in tracked stages
    #         try:
    #             stage = self._tracked_dyn_channels[guild][owner]
    #         except KeyError:
    #             logger.warning(
    #                 f"[{guild}] Could not delete stage owned by {owner}. Does not own any."
    #             )
    #             return
    #
    #     if owner is not None:
    #         # delete from tracked stages
    #         del self._tracked_dyn_channels[guild][owner]
    #
    #     logger.info(f"[{guild}] Deleting stage owned by {owner}: {stage}")
    #     await stage.delete()

    # async def delete_all_stages(self, category):
    #     """Delete all stage channels in category."""
    #     for channel in category.channels:
    #         if isinstance(channel, StageChannel):
    #             await self._delete_stage(stage=channel)
    #
    # async def delete_stage(self, owner, guild):
    #     """Delete stage channel owned by a given user."""
    #     await self._delete_stage(owner=owner, guild=guild)
    #
    # async def delete_old_stages(self, category):
    #     """Delete all old stages."""
    #     for stage in category.stage_channels:
    #         if (
    #             datetime.datetime.utcnow()
    #             - datetime.timedelta(minutes=self.category_info.stage_max_minutes)
    #             > stage.created_at
    #         ):
    #             logger.info(f"[{category.guild}] Delete old stage: {stage}")
    #             await self._delete_stage(stage=stage)
    #
    # async def delete_untracked_stages(self):
    #     """Delete all untracked stages. Untracked stages existed prior to bot login."""
    #     # TODO implement and maybe call this at login (for all guilds)? maybe also periodically?
