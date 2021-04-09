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
        logger.debug(
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

    def __init__(self, text):
        self._text = text
        self.message = None

    @property
    def text(self):
        return self._text

    async def set_text(self, value):
        """Set message text. Edits discord message in the process."""
        self._text = value
        await self.message.edit(content=self._text)

    async def send_and_wait(self, channel):
        # TODO how to limit reactions to the ones given? -> delete unknown reactions
        self.message = await channel.send(self.text)
        for emoji in ReactMessage.reactions.keys():
            await self.message.add_reaction(emoji)

        while True:
            reaction, user = await self.client.wait_for(
                "reaction_add",
                check=lambda reaction, user: reaction.message == self.message
                and str(reaction.emoji) in ReactMessage.reactions.keys()
                and user != self.client.user,
            )
            await ReactMessage.reactions[reaction.emoji](self, reaction, user)
