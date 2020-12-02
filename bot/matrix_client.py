import nio


class MatrixClient:

    def __init__(self, *args, **kwargs):
        self.client = nio.AsyncClient(*args, **kwargs)

    async def __aenter__(self) -> nio.AsyncClient:
        return self.client

    async def __aexit__(self, *args, **kwargs):
        await self.client.close()
