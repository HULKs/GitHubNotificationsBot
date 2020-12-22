import aiohttp
import links_from_header
import logging
import typing


class UnexpectedResponseStatus(Exception):

    def __init__(self, method: str, url: str, got: int, expected: int, body: str):
        super().__init__(
            f'Got {got} instead of {expected} while {method} {url} (body: {body})')
        self.url = url
        self.got = got
        self.expected = expected
        self.body = body


class GitHubApi:

    events = [
        'push',
        'issues',
        'pull_request',
        'issue_comment',
        'pull_request_review_comment',
        'pull_request_review',
        'fork',
    ]

    def __init__(self, access_token: str, *args, **kwargs):
        self.logger = logging.getLogger('GitHubApi')
        self.session = aiohttp.ClientSession(*args, **kwargs)
        self.access_token = access_token

    async def __aenter__(self) -> 'MatrixClient':
        await self.session.__aenter__()
        return self

    async def __aexit__(self, *args, **kwargs):
        await self.session.__aexit__(*args, **kwargs)

    async def forks(self, owner: str, repo: str):
        '''Retrieves forks recursively'''
        self.logger.info(f'Retrieving forks recursively for {owner}/{repo}...')
        url = f'https://api.github.com/repos/{owner}/{repo}/forks'
        result = []
        while url is not None:
            self.logger.debug(f'GET {url}...')
            async with self.session.get(url, headers={
                'Accept': 'application/vnd.github.v3+json',
                'Authorization': f'token {self.access_token}',
                'User-Agent': 'bot',
            }) as response:
                self.logger.debug(f'GET {url} -> {response.status}')
                if response.status != 200:
                    raise UnexpectedResponseStatus('GET', url, response.status, 200, await response.text())
                for fork in await response.json():
                    self.logger.info(
                        f'Found fork {fork["owner"]["login"]}/{fork["name"]}',
                    )
                    result.append((fork['owner']['login'], fork['name']))
                url = None
                if 'Link' in response.headers:
                    extracted_links = links_from_header.extract(
                        response.headers['Link'],
                    )
                    if 'next' in extracted_links:
                        self.logger.debug('Retrieving next page...')
                        url = extracted_links['next']
        for fork_owner, fork_repo in result:
            self.logger.debug(f'Recurse into {fork_owner}/{fork_repo}...')
            result += await self.forks(fork_owner, fork_repo)
        return result

    async def hooks(self, owner_or_org: str, repo: typing.Optional[str] = None):
        self.logger.info(
            f'Retrieving hooks for {owner_or_org}/{repo}...' if repo is not None else f'Retrieving hooks for {owner_or_org}...',
        )
        url = f'https://api.github.com/repos/{owner_or_org}/{repo}/hooks' if repo is not None else f'https://api.github.com/orgs/{owner_or_org}/hooks'
        result = []
        while url is not None:
            self.logger.debug(f'GET {url}...')
            async with self.session.get(url, headers={
                'Accept': 'application/vnd.github.v3+json',
                'Authorization': f'token {self.access_token}',
                'User-Agent': 'bot',
            }) as response:
                self.logger.debug(f'GET {url} -> {response.status}')
                if response.status != 200:
                    raise UnexpectedResponseStatus('GET', url, response.status, 200, await response.text())
                for hook in await response.json():
                    self.logger.info(
                        f'Found hook {hook["config"]["url"]} (events: {hook["events"]})',
                    )
                    result.append((hook['config']['url'], hook['events']))
                url = None
                if 'Link' in response.headers:
                    extracted_links = links_from_header.extract(
                        response.headers['Link'],
                    )
                    if 'next' in extracted_links:
                        self.logger.debug('Retrieving next page...')
                        url = extracted_links['next']
        return result
