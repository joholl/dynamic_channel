# SPDX-License-Identifier: GPL-3.0
import logging

logger = logging.getLogger(__name__)


class ReactionWrapper:
    def __init__(self, func, emoji, remove):
        self.func = func
        self.emoji = emoji
        self.remove = remove

    def __set_name__(self, owner, name):
        setattr(owner, name, self.wrapper)
        owner.reactions[self.emoji] = self.wrapper

    async def wrapper(self, other_self, *args, **kwargs):
        reaction, user = args
        logger.info(
            f"[{reaction.message.guild}] User {user} reacted to bot message: ({reaction})  --> {self.func.__name__}"
        )
        result = await self.func(other_self, *args, **kwargs)
        if self.remove:
            await reaction.remove(user)
        return result


def react_to(emoji, remove=False):
    def _decorator(func):
        return ReactionWrapper(func, emoji, remove)

    return _decorator


class ReactMessage:
    reactions = {}

    def __init__(self, client, get_text_cb):
        self._client = client
        self._get_text_cb = get_text_cb
        self.message = None

    @property
    def text(self):
        return self._get_text_cb()

    async def update_text(self):
        """Update discord message text."""
        text = self.text
        logger.info(f"[{self.message.guild}] Update bot control message in channel {self.message.channel}: {text}")
        await self.message.edit(content=text)

    async def send_and_wait(self, channel):
        text = self.text
        logger.info(f"[{channel.guild}] Create react message in channel {channel}: {text}")
        self.message = await channel.send(text)
        for emoji in ReactMessage.reactions.keys():
            await self.message.add_reaction(emoji)

        while True:
            reaction, user = await self._client.wait_for(
                "reaction_add",
                check=lambda reaction, user: reaction.message == self.message and user != self._client.user,
            )
            if reaction.emoji in ReactMessage.reactions:
                # call callback function (deleting reaction is up to callback)
                await ReactMessage.reactions[reaction.emoji](self, reaction, user)
            else:
                # always remove unknown reactions
                await reaction.remove(user)
