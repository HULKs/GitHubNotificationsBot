import asyncio
import click
import getpass
import nio
import pathlib
import socket


async def matrix_login(arguments):
    client = nio.AsyncClient(
        homeserver=arguments['matrix_homeserver'],
        user=arguments['matrix_user_id'],
        store_path=arguments['matrix_store_path'],
    )
    try:
        response = await client.login(
            password=arguments['matrix_password'],
            device_name=arguments['matrix_device_name'],
        )
        if isinstance(response, nio.LoginResponse):
            if client.should_upload_keys:
                print('Should upload keys...')
                await client.keys_upload()
            if client.should_query_keys:
                print('Should query keys...')
                await client.keys_query()
            if client.should_claim_keys:
                print('Should claim keys...')
                await client.keys_claim()
            print('Syncing full state...')
            await client.sync(full_state=True)
            print(f'MATRIX_HOMESERVER={arguments["matrix_homeserver"]}')
            print(f'MATRIX_USER_ID={response.user_id}')
            print(f'MATRIX_DEVICE_ID={response.device_id}')
            print(f'MATRIX_ACCESS_TOKEN={response.access_token}')
        else:
            print(response)
    finally:
        await client.close()


@click.command()
@click.option('--matrix-homeserver', required=True, envvar='MATRIX_HOMESERVER')
@click.option('--matrix-user-id', required=True, envvar='MATRIX_USER_ID')
@click.option('--matrix-device-name', default=f'{getpass.getuser()}@{socket.gethostname()}', envvar='MATRIX_DEVICE_NAME')
@click.option('--matrix-store-path', required=True, envvar='MATRIX_STORE_PATH')
@click.option('--matrix-password', prompt=True, hide_input=True, envvar='MATRIX_PASSWORD')
def main(**arguments):
    asyncio.run(matrix_login(arguments))
