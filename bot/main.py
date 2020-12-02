import aiogram
import asyncio
import click
import nio

from .matrix_client import MatrixClient
from .telegram_client import TelegramClient


async def send(arguments):
    async with TelegramClient(token=arguments['telegram_bot_token']) as client:
        client: aiogram.Bot
        print(await client.get_me())
        await client.send_message(chat_id=arguments['telegram_chat_id'], text='Hello World!')
    # async with MatrixClient(homeserver=arguments['matrix_homeserver'], user=arguments['matrix_user_id'], device_id=arguments['matrix_device_id']) as client:
    #     client: nio.AsyncClient
    #     client.user_id = arguments['matrix_user_id']
    #     client.access_token = arguments['matrix_access_token']
    #     await client.room_send(
    #         room_id=arguments['matrix_room_id'],
    #         message_type='m.room.message',
    #         content={
    #             'msgtype': 'm.text',
    #             'body': 'Hello World',
    #         },
    #     )


@click.command()
@click.option('--telegram-bot-token', required=True, envvar='TELEGRAM_BOT_TOKEN')
@click.option('--telegram-chat-id', required=True, envvar='TELEGRAM_CHAT_ID')
@click.option('--matrix-homeserver', required=True, envvar='MATRIX_HOMESERVER')
@click.option('--matrix-user-id', required=True, envvar='MATRIX_USER_ID')
@click.option('--matrix-device-id', required=True, envvar='MATRIX_DEVICE_ID')
@click.option('--matrix-device-name', required=True, envvar='MATRIX_DEVICE_NAME')
@click.option('--matrix-access-token', required=True, envvar='MATRIX_ACCESS_TOKEN')
@click.option('--matrix-room-id', required=True, envvar='MATRIX_ROOM_ID')
def main(**arguments):
    asyncio.run(send(arguments))
