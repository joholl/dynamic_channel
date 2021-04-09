# dynamic_channel

A friendly discord bot to enable your members to create their personal stages!

Since 2021, [Discord supports stage
channels](https://support.discord.com/hc/en-us/articles/1500005513722-Stage-Channels-FAQ).
However, only _stage moderators_ can invite people to speak. That is, admins,
mods and people promoted by the aforementioned. There is currently no native
support for dynamically creating stages where normal users can guide the
conversation.

The `dynamic_channel` discord bot enables users to create their own personal
stage. On their own stage, users can invite any other member onto the stage.
These members can then speak but not invite. Enable your users to create guided
topic discussions!

Users can either delete their stages or have them cleaned up automagically by
the bot after a while.

## Getting started

Install the dependencies.

```bash
pip install -r requirements.txt
```

Run the bot.

```bash
python -m dynamic_channel
```

## How it works

On logon, the bot creates a category with a read-only text channel. The bot
posts a control message, there. Users can react with emojis to this message to
create/delete a stage in the same category.

## Settings

Edit the `.env` settings file to enter your bot token, the bot message etc.

## Permissions

The bot requires the following permissions:

* manage server
* manage roles
* manage channels
* send messages
* manage messages
* add reactions
* mute members
* deafen members
* move members