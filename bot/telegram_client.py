import aiogram


class TelegramClient:

    def __init__(self, *args, **kwargs):
        self.bot = aiogram.Bot(*args, **kwargs)

    async def __aenter__(self) -> aiogram.Bot:
        return self.bot

    async def __aexit__(self, *args, **kwargs):
        await self.bot.close()
