import asyncio
import click
import nio

from .matrix_client import MatrixClient


async def matrix_login(arguments):
    async with MatrixClient(homeserver=arguments['matrix_homeserver'], user=arguments['matrix_user_id']) as client:
        response = await client.login(
            password=arguments['matrix_password'],
            device_name=arguments['matrix_device_name'],
        )
        if isinstance(response, nio.LoginResponse):
            print()
            print(f'MATRIX_HOMESERVER={arguments["matrix_homeserver"]}')
            print(f'MATRIX_USER_ID={response.user_id}')
            print(f'MATRIX_DEVICE_ID={response.device_id}')
            print(f'MATRIX_ACCESS_TOKEN={response.access_token}')
        else:
            print(response)


@click.command()
@click.option('--matrix-homeserver', required=True, envvar='MATRIX_HOMESERVER')
@click.option('--matrix-user-id', required=True, envvar='MATRIX_USER_ID')
@click.option('--matrix-device-name', default='bot', envvar='MATRIX_DEVICE_NAME')
@click.option('--matrix-password', prompt=True, hide_input=True, envvar='MATRIX_PASSWORD')
def main(**arguments):
    asyncio.run(matrix_login(arguments))
