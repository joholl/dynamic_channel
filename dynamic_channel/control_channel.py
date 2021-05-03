# SPDX-License-Identifier: GPL-3.0
import asyncio
import logging

from dynamic_channel.message import ReactMessage, react_to

logger = logging.getLogger(__name__)


class ControlMessage(ReactMessage):
    def __init__(
        self, control_channel, get_text_cb
    ):  # TODO shouldn't this class (and its parent) work with a text model (here get_text() callback)?
        super().__init__(control_channel.client, get_text_cb)
        self.control_channel = control_channel

    @property
    def client(self):
        return self.control_channel.client

    @react_to("🆕", remove=True)
    async def create_dyn_channel(self, _reaction, user):
        await self.client.create_dyn_channel(user=user, control_channel=self.control_channel)
        await self.update_text()

    @react_to("❌", remove=True)
    async def delete_stage(self, _reaction, user):
        await self.client.delete_dyn_channel(user=user, control_channel=self.control_channel)
        await asyncio.sleep(0.1)
        await self.update_text()

    # @react_to("🗑️️️", remove=True)
    @react_to("🔥", remove=True)
    async def delete_all_stages(self, _reaction, user):
        await self.client.delete_all_channels(user=user, control_channel=self.control_channel)
        await asyncio.sleep(0.1)
        await self.update_text()

    # @react_to("🔄", remove=True)
    # async def reload(self, reaction, user):
    #     await self.update_text()


class ControlChannel:
    def __init__(self, dyn_category, text_channel, get_text_cb):
        """If control_message is None, the control channel will be reset (i.e. posting the control message)."""
        self.dyn_category = dyn_category
        self.text_channel = text_channel
        self._get_text_cb = get_text_cb
        self._control_message = None

    @property
    def client(self):  # TODO align these, i.e. dyn_ naming convention
        return self.dyn_category.client

    @property
    def guild(self):
        return self.dyn_category.guild

    @property
    async def control_message(self):
        if self._control_message is not None:
            return self._control_message

        # delete all prior messages in the same text channel (except the last one if it is by the bot)
        async for message in self.text_channel.history().filter(lambda msg: msg.author == self.client.user):
            logger.info(f"[{self.text_channel.guild}] Deleting prior bot control message: {message}")
            await message.delete()

        # post new bot control message
        text = self._get_text_cb()
        logger.info(
            f"[{self.text_channel.guild}] Posting new bot control message in channel {self.text_channel}: {text}"
        )

        self._control_message = ControlMessage(control_channel=self, get_text_cb=self._get_text_cb)
        loop = asyncio.get_event_loop()
        loop.create_task(self._control_message.send_and_wait(self.text_channel))
