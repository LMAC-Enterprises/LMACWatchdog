import discord as discord
from discord.ext import tasks


class DiscordMessage:
    _message: str
    _channelId: int

    def __init__(self, message: str, channelId: int):
        self._message = message
        self._channelId = channelId

    @property
    def message(self):
        return self._message

    @property
    def channelId(self):
        return self._channelId


class DiscordMessageTransponder(discord.Client):
    _channelId: int
    _messages: list

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._messages = kwargs['messages']
        print(self._messages)
        print(kwargs)
        # start the task to run in the background
        self.my_background_task.start()

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

    @tasks.loop(seconds=5)
    async def my_background_task(self):
        nextMessage: DiscordMessage = None
        try:
            nextMessage = self._messages.pop(0)
        except IndexError:
            await self.close()
            return

        channel = self.get_channel(nextMessage.channelId)
        await channel.send(nextMessage.message)

    @my_background_task.before_loop
    async def before_my_task(self):
        await self.wait_until_ready()


class DiscordDispatcher:
    _instance = None
    _messageQueue: list
    _channelId: int

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DiscordDispatcher, cls).__new__(cls)
            cls._messageQueue = []

        return cls._instance

    def enqueueMessage(self, message: str):
        print(message)
        self._messageQueue.append(DiscordMessage(message, self._channelId))

    def enterChatroom(self, channelId: int):
        self._channelId = channelId

    def processMessages(self, discordToken):
        transponder = DiscordMessageTransponder(messages=self._messageQueue)
        transponder.run(discordToken)
