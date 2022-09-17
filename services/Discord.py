from typing import Any

import discord as discord
from discord import Intents
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

    def __str__(self):
        return 'Discord message: {message}'.format(message=self._message)

    def __repr__(self):
        return self.__str__()


class DiscordMessageTransponder(discord.Client):
    _channelId: int
    _messages: list

    def __init__(self, *, intents: Intents, **options: Any):
        super().__init__(intents=intents, **options)

        self._messages = options['messages']
        # start the task to run in the background


    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')
        self._sendMessagesTask.start()

    @tasks.loop(seconds=5)
    async def _sendMessagesTask(self):
        nextMessage: DiscordMessage = None
        try:
            nextMessage = self._messages.pop(0)
        except IndexError:
            await self.close()
            return

        channel = self.get_channel(nextMessage.channelId)
        await channel.send(nextMessage.message)

    @_sendMessagesTask.before_loop
    async def _beforeSendMessagesTask(self):
        await self.wait_until_ready()


class DiscordDispatcher:
    _instance = None
    _messageQueue: list
    _channelId: int
    _simulate: bool

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DiscordDispatcher, cls).__new__(cls)
            cls._messageQueue = []
            cls._simulate = False
            cls._channelId = 0

        return cls._instance

    def enqueueMessage(self, message: str):
        self._messageQueue.append(DiscordMessage(message, self._channelId))

    def enterChatroom(self, channelId: int):
        self._channelId = channelId

    def runDiscordTasks(self, discordToken: str):
        if self._simulate:
            print('Running discord tasks: {tasks}'.format(tasks=str(self._messageQueue)))
            return

        if len(self._messageQueue) == 0:
            return

        intents = discord.Intents.default()

        transponder = DiscordMessageTransponder(messages=self._messageQueue, intents=intents)
        transponder.run(discordToken)

    def setSimulationMode(self, simulate: bool):
        self._simulate = simulate
