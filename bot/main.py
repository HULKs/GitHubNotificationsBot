import aiohttp.web
import asyncio
import click
import hashlib
import hmac

from .matrix_client import MatrixClient
from .telegram_client import TelegramClient


class Bot:

    def __init__(self, arguments: dict):
        self.arguments = arguments
        self.api_session = aiohttp.ClientSession()
        self.telegram = TelegramClient(
            chat_id=self.arguments['telegram_chat_id'],
            token=self.arguments['telegram_bot_token'],
        )
        self.matrix = MatrixClient(
            user_id=self.arguments['matrix_user_id'],
            access_token=self.arguments['matrix_access_token'],
            room_id=self.arguments['matrix_room_id'],
            homeserver=self.arguments['matrix_homeserver'],
            user=self.arguments['matrix_user_id'],
            device_id=self.arguments['matrix_device_id'],
        )

    def add_routes(self, app: aiohttp.web.Application):
        app.add_routes([
            aiohttp.web.post(
                '/',
                self.handle,
            ),
        ])

    async def __aenter__(self):
        await self.api_session.__aenter__()
        await self.telegram.__aenter__()
        await self.matrix.__aenter__()
        await self.telegram.send_startup()
        await self.matrix.send_startup()
        await self.update_hooks()
        return self

    async def __aexit__(self, *args, **kwargs):
        await self.matrix.__aexit__(*args, **kwargs)
        await self.telegram.__aexit__(*args, **kwargs)
        await self.api_session.__aexit__(*args, **kwargs)

    async def authenticate(self, request: aiohttp.web.Request):
        own_signature = 'sha256=' + hmac.new(
            key=self.arguments['github_webhook_secret'].encode(),
            msg=await request.read(),
            digestmod=hashlib.sha256,
        ).hexdigest()
        sent_signature = request.headers['X-Hub-Signature-256']
        if own_signature != sent_signature:
            await self.telegram.send_unauthorized_request(request.remote)
            await self.matrix.send_unauthorized_request(request.remote)
            raise aiohttp.web.HTTPForbidden

    async def handle(self, request: aiohttp.web.Request):
        await self.authenticate(request)
        event = request.headers['X-Github-Event']
        payload = await request.json()
        if event == 'ping':
            return await self.handle_ping(payload)
        elif event == 'push':
            return await self.handle_push(payload)
        elif event == 'issues' or event == 'pull_request':
            return await self.handle_issue_or_pull_request(payload)
        elif event == 'issue_comment' or event == 'pull_request_review_comment':
            return await self.handle_issue_or_pull_request_comment(payload)
        elif event == 'pull_request_review':
            return await self.handle_pull_request_review(payload)
        elif event == 'fork':
            return await self.handle_fork(payload)
        # silently ignore unimplemented events
        raise aiohttp.web.HTTPOk

    async def handle_ping(self, payload: dict):
        return aiohttp.web.Response()

    async def handle_push(self, payload: dict):
        pusher = payload['pusher']['name']
        commit_messages = [commit['message'].split(
            '\n')[0] for commit in payload['commits']]
        branch = payload['ref'].split('/')[-1]
        repository = payload['repository']['full_name']
        await self.telegram.send_push(pusher, commit_messages, branch, repository)
        await self.matrix.send_push(pusher, commit_messages, branch, repository)
        return aiohttp.web.Response()

    async def handle_issue_or_pull_request(self, payload: dict):
        if payload['action'] not in ['opened', 'closed', 'reopened']:
            return aiohttp.web.Response()
        sender = payload['sender']['login']
        type = 'pull request' if 'pull_request' in payload else 'issue'
        action = 'merged' if 'pull_request' in payload and payload[
            'action'] == 'closed' and payload['pull_request']['merged'] else payload['action']
        repository = payload['repository']['full_name']
        number = payload['pull_request']['number'] if 'pull_request' in payload else payload['issue']['number']
        title = payload['pull_request']['title'] if 'pull_request' in payload else payload['issue']['title']
        url = payload['pull_request']['html_url'] if 'pull_request' in payload else payload['issue']['html_url']
        await self.telegram.send_issue_or_pull_request(sender, type, action, repository, number, title, url)
        await self.matrix.send_issue_or_pull_request(sender, type, action, repository, number, title, url)
        return aiohttp.web.Response()

    async def handle_issue_or_pull_request_comment(self, payload: dict):
        if payload['action'] != 'created':
            return aiohttp.web.Response()
        commenter = payload['comment']['user']['login']
        type = 'pull request' if 'pull_request' in payload else 'issue'
        repository = payload['repository']['full_name']
        number = payload['pull_request']['number'] if 'pull_request' in payload else payload['issue']['number']
        title = payload['pull_request']['title'] if 'pull_request' in payload else payload['issue']['title']
        body = payload['comment']['body']
        url = payload['comment']['html_url']
        await self.telegram.send_issue_or_pull_request_comment(commenter, type, repository, number, title, body, url)
        await self.matrix.send_issue_or_pull_request_comment(commenter, type, repository, number, title, body, url)
        return aiohttp.web.Response()

    async def handle_pull_request_review(self, payload: dict):
        state = payload['review']['state']
        if payload['review']['state'] == 'changes_requested':
            state = 'requested changes on'
        elif payload['review']['state'] == 'commented':
            state = 'commented on'
        sender = payload['sender']['login']
        repository = payload['repository']['full_name']
        number = payload['pull_request']['number']
        title = payload['pull_request']['title']
        body = payload['review']['body']
        url = payload['review']['html_url']
        await self.telegram.send_pull_request_review(sender, state, repository, number, title, body, url)
        await self.matrix.send_pull_request_review(sender, state, repository, number, title, body, url)
        return aiohttp.web.Response()

    async def handle_fork(self, payload: dict):
        await self.update_hooks()
        # TODO: fork
        return aiohttp.web.Response()

    async def get_from_api(self, url: str, additional_headers: dict = {}, additional_params: dict = {}, expected_response_status=200):
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'Authorization': f'token {self.arguments["github_access_token"]}',
            'User-Agent': 'bot',
        }
        headers.update(additional_headers)
        async with self.api_session.get(f'https://api.github.com{url}', headers=headers, params=additional_params) as response:
            if response.status != expected_response_status:
                await self.telegram.send_failed_api_call('GET', url, response.status, expected_response_status)
                await self.matrix.send_failed_api_call('GET', url, response.status, expected_response_status)
                raise RuntimeError(f'Got {response.status} instead of {expected_response_status} while GET https://api.github.com{url} (body: {await response.json()}')
            return await response.json()

    async def post_from_api(self, url: str, additional_headers: dict = {}, additional_params: dict = {}, json: dict = None, expected_response_status=200):
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'Authorization': f'token {self.arguments["github_access_token"]}',
            'User-Agent': 'bot',
        }
        headers.update(additional_headers)
        async with self.api_session.post(f'https://api.github.com{url}', headers=headers, params=additional_params, json=json) as response:
            if response.status != expected_response_status:
                await self.telegram.send_failed_api_call('POST', url, response.status, expected_response_status)
                await self.matrix.send_failed_api_call('POST', url, response.status, expected_response_status)
                raise RuntimeError(f'Got {response.status} instead of {expected_response_status} while POST https://api.github.com{url} (body: {await response.json()}')
            return await response.json()

    async def get_repositories_of_organization(self, org: str):
        return [
            repository['name']
            for repository in await self.get_from_api(f'/orgs/{org}/repos')
        ]

    async def get_forks_of_repository(self, owner: str, repo: str):
        return [
            (fork['owner']['login'], fork['name'])
            for fork in await self.get_from_api(f'/repos/{owner}/{repo}/forks')
        ]

    async def check_hooks_of_repository(self, owner: str, repo: str):
        for hook in await self.get_from_api(f'/repos/{owner}/{repo}/hooks'):
            if hook['config']['url'] == self.arguments['github_webhook_url']:
                return True
        return False

    async def check_hooks_of_organization(self, org: str):
        for hook in await self.get_from_api(f'/orgs/{org}/hooks'):
            if hook['config']['url'] == self.arguments['github_webhook_url']:
                return True
        return False

    async def create_hook_of_repository(self, owner: str, repo: str):
        await self.post_from_api(f'/repos/{owner}/{repo}/hooks', json={
            'name': 'web',
            'config': {
                'url': self.arguments['github_webhook_url'],
                'content_type': 'json',
                'secret': self.arguments['github_webhook_secret'],
            },
            'events': ['*'],
        }, expected_response_status=201)

    async def create_hook_of_organization(self, org: str):
        await self.post_from_api(f'/orgs/{org}/hooks', json={
            'name': 'web',
            'config': {
                'url': self.arguments['github_webhook_url'],
                'content_type': 'json',
                'secret': self.arguments['github_webhook_secret'],
            },
            'events': ['*'],
        }, expected_response_status=201)

    async def update_hooks_of_repository(self, owner: str, repo: str):
        for fork_owner, fork_repo in await self.get_forks_of_repository(owner, repo):
            if not await self.check_hooks_of_repository(fork_owner, fork_repo):
                await self.telegram.send_create_webhook_of_repository(fork_owner, fork_repo)
                await self.matrix.send_create_webhook_of_repository(fork_owner, fork_repo)
                await self.create_hook_of_repository(fork_owner, fork_repo)

    async def update_hooks(self):
        if not await self.check_hooks_of_organization(self.arguments['github_organization']):
            await self.telegram.send_create_webhook_of_organization(self.arguments['github_organization'])
            await self.matrix.send_create_webhook_of_organization(self.arguments['github_organization'])
            await self.create_hook_of_organization(self.arguments['github_organization'])
        for repo in self.arguments['github_forkable_repositories'].split(','):
            await self.update_hooks_of_repository(self.arguments['github_organization'], repo)


async def async_main(arguments):
    app = aiohttp.web.Application()

    async with Bot(arguments) as bot:
        bot.add_routes(app)

        runner = aiohttp.web.AppRunner(app)
        await runner.setup()
        site = aiohttp.web.TCPSite(
            runner=runner,
            host=arguments['github_webhook_host'],
            port=arguments['github_webhook_port'],
        )
        await site.start()

        eternity_event = asyncio.Event()
        try:
            print('Listening on', ', '.join(str(site.name)
                                            for site in runner.sites), '...')
            await eternity_event.wait()
        finally:
            await runner.cleanup()


@click.command()
@click.option('--github-webhook-host', required=True, envvar='GITHUB_WEBHOOK_HOST')
@click.option('--github-webhook-port', type=int, required=True, envvar='GITHUB_WEBHOOK_PORT')
@click.option('--github-webhook-secret', required=True, envvar='GITHUB_WEBHOOK_SECRET')
@click.option('--github-access-token', required=True, envvar='GITHUB_ACCESS_TOKEN')
@click.option('--github-organization', required=True, envvar='GITHUB_ORGANIZATION')
@click.option('--github-forkable-repositories', required=True, envvar='GITHUB_FORKABLE_REPOSITORIES')
@click.option('--github-webhook-url', required=True, envvar='GITHUB_WEBHOOK_URL')
@click.option('--telegram-bot-token', required=True, envvar='TELEGRAM_BOT_TOKEN')
@click.option('--telegram-chat-id', required=True, envvar='TELEGRAM_CHAT_ID')
@click.option('--matrix-homeserver', required=True, envvar='MATRIX_HOMESERVER')
@click.option('--matrix-user-id', required=True, envvar='MATRIX_USER_ID')
@click.option('--matrix-device-id', required=True, envvar='MATRIX_DEVICE_ID')
@click.option('--matrix-access-token', required=True, envvar='MATRIX_ACCESS_TOKEN')
@click.option('--matrix-room-id', required=True, envvar='MATRIX_ROOM_ID')
def main(**arguments):
    # TODO: handle signals to terminate gracefully
    asyncio.run(async_main(arguments))
