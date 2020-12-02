import click


@click.command()
@click.option('--telegram-bot-token', required=True, envvar='TELEGRAM_BOT_TOKEN')
@click.option('--telegram-chat-id', required=True, envvar='TELEGRAM_CHAT_ID')
@click.option('--matrix-user-id', required=True, envvar='MATRIX_USER_ID')
@click.option('--matrix-homeserver', required=True, envvar='MATRIX_HOMESERVER')
@click.option('--matrix-device-id', required=True, envvar='MATRIX_DEVICE_ID')
@click.option('--matrix-access-token', required=True, envvar='MATRIX_ACCESS_TOKEN')
def main(**arguments):
    print(arguments)
