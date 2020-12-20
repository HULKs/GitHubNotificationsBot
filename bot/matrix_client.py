import nio
import typing


class MatrixClient:

    def __init__(self, user_id: str, access_token: str, room_id: str, *args, **kwargs):
        self.client = nio.AsyncClient(*args, **kwargs)
        self.client.user_id = user_id
        self.client.access_token = access_token
        self.room_id = room_id

    async def __aenter__(self) -> 'MatrixClient':
        return self

    async def __aexit__(self, *args, **kwargs):
        await self.client.close()

    async def send(self, message: str, formatted_message: str, **kwargs):
        await self.client.room_send(
            room_id=self.room_id,
            message_type='m.room.message',
            content={
                'msgtype': 'm.text',
                'body': message,
                'format': 'org.matrix.custom.html',
                'formatted_body': formatted_message,
            },
        )
        # await self.bot.send_message(chat_id=self.chat_id, text=message, parse_mode='MarkdownV2', **kwargs)

    async def send_startup(self):
        await self.send(
            '\U0001f92b Online again',
            '\U0001f92b Online again',
        )

    async def send_unauthorized_request(self, remote: str):
        await self.send(
            f'\U000026a0 Unauthorized request from `{self.escape(remote)}`',
            f'\U000026a0 Unauthorized request from <code>{self.escape(remote)}</code>',
        )

    async def send_failed_api_call(self, method: str, url: str, got: int, expected: int):
        await self.send(
            f'\U000026a0 Failed API call {method} {self.escape(url)} (got `{got}`, expected `{expected}`)',
            f'\U000026a0 Failed API call {method} {self.escape(url)} (got <code>{got}</code>, expected <code>{expected}</code>)',
        )

    async def send_create_webhook_of_repository(self, fork_owner: str, fork_repo: str):
        await self.send(
            f'\U000026a0 Creating webhook at `{self.escape(fork_owner)}/{self.escape(fork_repo)}`...',
            f'\U000026a0 Creating webhook at <code>{self.escape(fork_owner)}/{self.escape(fork_repo)}</code>...',
        )

    async def send_create_webhook_of_organization(self, organization: str):
        await self.send(
            f'\U000026a0 Creating webhook at `{self.escape(organization)}`...',
            f'\U000026a0 Creating webhook at <code>{self.escape(organization)}</code>...',
        )

    async def send_push(self, pusher: str, commit_messages: typing.List[str], branch: str, repository: str):
        escaped_commit_messages_markdown = '\n'.join(
            [f'- `{self.escape(message)}`' for message in commit_messages],
        )
        escaped_commit_messages_html = '<br />'.join(
            [f'- <code>{self.escape(message)}</code>' for message in commit_messages],
        )
        commit_label = 'commits' if len(commit_messages) > 1 else 'commit'
        await self.send(
            f'`@{pusher}` pushed {len(commit_messages)} {commit_label} to `{branch}` at `{repository}`:\n\n{escaped_commit_messages_markdown}',
            f'<code>@{self.escape(pusher)}</code> pushed {len(commit_messages)} {commit_label} to <code>{self.escape(branch)}</code> at <code>{self.escape(repository)}</code>:<br /><br />{escaped_commit_messages_html}',
        )

    async def send_issue_or_pull_request(self, sender: str, type: str, action: str, repository: str, number: int, title: str, url: str):
        await self.send(
            f'`@{sender}` {action} {type} `{repository}#{number}` (`{title}`):\n\n{url}',
            f'<code>@{self.escape(sender)}</code> {self.escape(action)} {type} <code>{self.escape(repository)}#{number}</code> (<code>{self.escape(title)}</code>):<br /><br /><a href="{url}">{self.escape(url)}</a>',
        )
        # TODO: merge

    async def send_issue_or_pull_request_comment(self, commenter: str, type: str, repository: str, number: int, title: str, body: str, url: str):
        escaped_body = self.escape(body).replace('\n', '<br />')
        await self.send(
            f'`@{commenter}` commented on {type} `{repository}#{number}` (`{title}`):\n\n{body}\n\n{url}',
            f'<code>@{self.escape(commenter)}</code> commented on {type} <code>{self.escape(repository)}#{number}</code> (<code>{self.escape(title)}</code>):<br /><br />{escaped_body}<br /><br /><a href="{url}">{self.escape(url)}</a>',
        )

    async def send_pull_request_review(self, sender: str, state: str, repository: str, number: int, title: str, body: str, url: str):
        escaped_body = self.escape(body).replace('\n', '<br />')
        await self.send(
            f'`@{sender}` {state} pull request `{repository}#{number}` (`{title}`):\n\n{body}\n\n{url}',
            f'<code>@{self.escape(sender)}</code> {state} pull request <code>{self.escape(repository)}#{number}</code> (<code>{self.escape(title)}</code>):<br /><br />{escaped_body}<br /><br /><a href="{url}">{self.escape(url)}</a>',
        )

    def escape(self, message: str):
        return message.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace('\'', '&#x27;')
