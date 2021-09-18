import nio
import typing


class MatrixClient:

    def __init__(self, user_id: str, access_token: str, room_id_discussions: str, room_id_pushes: str, *args, **kwargs):
        self.client = nio.AsyncClient(*args, **kwargs)
        self.client.user_id = user_id
        self.client.access_token = access_token
        self.room_id_discussions = room_id_discussions
        self.room_id_pushes = room_id_pushes

    async def __aenter__(self) -> 'MatrixClient':
        return self

    async def __aexit__(self, *args, **kwargs):
        await self.client.close()

    async def send_to_discussions(self, message: str, formatted_message: str, **kwargs):
        await self.client.room_send(
            room_id=self.room_id_discussions,
            message_type='m.room.message',
            content={
                'msgtype': 'm.text',
                'body': message,
                'format': 'org.matrix.custom.html',
                'formatted_body': formatted_message,
            },
        )

    async def send_to_pushes(self, message: str, formatted_message: str, **kwargs):
        await self.client.room_send(
            room_id=self.room_id_pushes,
            message_type='m.room.message',
            content={
                'msgtype': 'm.text',
                'body': message,
                'format': 'org.matrix.custom.html',
                'formatted_body': formatted_message,
            },
        )

    async def send_startup(self):
        await self.send_to_discussions(
            '\U0001f92b Online again',
            '\U0001f92b Online again',
        )
        await self.send_to_pushes(
            '\U0001f92b Online again',
            '\U0001f92b Online again',
        )

    async def send_unauthorized_request(self, remote: str):
        await self.send_to_pushes(
            f'\U000026a0 Unauthorized request from `{self.escape(remote)}`',
            f'\U000026a0 Unauthorized request from <code>{self.escape(remote)}</code>',
        )

    async def send_create_webhook_of_repository(self, fork_owner: str, fork_repo: str):
        await self.send_to_pushes(
            f'\U000026a0 Creating webhook at `{self.escape(fork_owner)}/{self.escape(fork_repo)}`...',
            f'\U000026a0 Creating webhook at <code>{self.escape(fork_owner)}/{self.escape(fork_repo)}</code>...',
        )

    async def send_create_webhook_of_organization(self, organization: str):
        await self.send_to_pushes(
            f'\U000026a0 Creating webhook at `{self.escape(organization)}`...',
            f'\U000026a0 Creating webhook at <code>{self.escape(organization)}</code>...',
        )

    async def send_push(self, pusher: str, commit_messages: typing.List[str], commits_url: str, branch: str, branch_url: str, repository: str, repository_url: str, is_forced: bool):
        escaped_commit_messages_markdown = '\n'.join(
            [f'- `{message}`' for message in commit_messages[-10:]],
        )
        escaped_commit_messages_html = '<br />'.join(
            [f'- <code>{self.escape(message)}</code>' for message in commit_messages[-10:]],
        )
        if len(commit_messages) > 10:
            escaped_commit_messages_markdown = f'... {len(commit_messages) - 10} more\n' + \
                escaped_commit_messages_markdown
            escaped_commit_messages_html = f'... {len(commit_messages) - 10} more<br />' + \
                escaped_commit_messages_html
        commit_label = 'commits' if len(commit_messages) > 1 else 'commit'
        force_label = 'force ' if is_forced else ''
        await self.send_to_pushes(
            f'`@{pusher}` {force_label}pushed [{len(commit_messages)} {commit_label}]({commits_url}) to [{branch}]({branch_url}) at [{repository}]({repository_url}):\n\n{escaped_commit_messages_markdown}',
            f'<code>@{self.escape(pusher)}</code> {force_label}pushed <a href="{commits_url}">{len(commit_messages)} {commit_label}</a> to <a href="{branch_url}">{self.escape(branch)}</a> at <a href="{repository_url}">{self.escape(repository)}</a>:<br /><br />{escaped_commit_messages_html}',
        )

    async def send_issue_or_pull_request(self, sender: str, type: str, action: str, repository: str, number: int, title: str, url: str):
        await self.send_to_discussions(
            f'`@{sender}` {action} {type} `{title}` ([{repository}#{number}]({url}))',
            f'<code>@{self.escape(sender)}</code> {self.escape(action)} {type} <code>{self.escape(title)}</code> (<a href="{url}">{self.escape(repository)}#{number}</a>)',
        )
        # TODO: merge

    async def send_issue_or_pull_request_comment(self, commenter: str, type: str, repository: str, number: int, title: str, body: typing.Optional[str], comment_url: str, url: str):
        escaped_body_markdown = f':\n\n`{body.strip()}`' if body is not None and len(body.strip()) > 0 else ''
        escaped_body_html = self.escape(body.strip()).replace("\n", "<br />")
        escaped_body_html = f':<br /><br /><code>{escaped_body_html}</code>' if body is not None and len(body.strip()) > 0 else ''
        await self.send_to_discussions(
            f'`@{commenter}` [commented on {type}]({comment_url}) `{title}` ([{repository}#{number}]({url})){escaped_body_markdown}',
            f'<code>@{self.escape(commenter)}</code> <a href="{comment_url}">commented on {type}</a> <code>{self.escape(title)}</code> (<a href="{url}">{self.escape(repository)}#{number}</a>){escaped_body_html}',
        )

    async def send_pull_request_review(self, sender: str, state: str, repository: str, number: int, title: str, body: typing.Optional[str], comment_url: str, url: str):
        escaped_body_markdown = f':\n\n`{body.strip()}`' if body is not None and len(body.strip()) > 0 else ''
        escaped_body_html = self.escape(body.strip()).replace("\n", "<br />")
        escaped_body_html = f':<br /><br /><code>{escaped_body_html}</code>' if body is not None and len(body.strip()) > 0 else ''
        await self.send_to_discussions(
            f'`@{sender}` [{state} pull request]({comment_url}) `{title}` ([{repository}#{number}]({url})){escaped_body_markdown}',
            f'<code>@{self.escape(sender)}</code> <a href="{comment_url}">{state} pull request</a> <code>{self.escape(title)}</code> (<a href="{url}">{self.escape(repository)}#{number}</a>){escaped_body_html}',
        )

    def escape(self, message: str):
        return message.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace('\'', '&#x27;')
