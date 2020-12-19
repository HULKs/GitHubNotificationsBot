import aiogram
import typing
import re


class TelegramClient:

    def __init__(self, chat_id: str, *args, **kwargs):
        self.chat_id = chat_id
        self.bot = aiogram.Bot(*args, **kwargs)

    async def __aenter__(self) -> aiogram.Bot:
        return self

    async def __aexit__(self, *args, **kwargs):
        await self.bot.close()

    async def send(self, message: str, **kwargs):
        await self.bot.send_message(chat_id=self.chat_id, text=message, parse_mode='MarkdownV2', **kwargs)

    async def send_unauthorized_request(self, remote: str):
        await self.send(f'\U000026a0 Unauthorized request from `{self.escape(remote)}`', disable_notification=True)

    async def send_unimplemented_event(self, event: str):
        await self.send(f'\U000026a0 Event {self.escape(event)} is not implemented', disable_notification=True)

    async def send_push(self, pusher: str, commit_messages: typing.List[str], branch: str, repository: str):
        escaped_pusher = f'`@{self.escape(pusher)}`'
        escaped_commit_messages = '\n'.join(
            [f'\\- `{self.escape(message)}`' for message in commit_messages],
        )
        commit_label = 'commits' if len(commit_messages) > 1 else 'commit'
        escaped_branch = f'`{self.escape(branch)}`'
        escaped_repository = f'`{self.escape(repository)}`'
        await self.send(f'{escaped_pusher} pushed {len(commit_messages)} {commit_label} to {escaped_branch} at {escaped_repository}:\n\n{escaped_commit_messages}')

    async def send_issue_or_pull_request(self, sender: str, type: str, action: str, repository: str, number: int, title: str, url: str):
        escaped_sender = f'`@{self.escape(sender)}`'
        escaped_action = self.escape(action)
        escaped_issue_or_pull_request = f'`{self.escape(repository)}#{number}`'
        escaped_title = f'`{self.escape(title)}`'
        converted_url = f'[{self.escape(url)}]({url})'
        print(f'{escaped_sender} {escaped_action} {type} {escaped_issue_or_pull_request}: {escaped_title}\n{converted_url}')
        await self.send(f'{escaped_sender} {escaped_action} {type} {escaped_issue_or_pull_request}: {escaped_title}\n{converted_url}')
        # TODO: merge

    async def send_issue_or_pull_request_comment(self, commenter: str, type: str, repository: str, number: int, title: str, body: str, url: str):
        escaped_commenter = f'`@{self.escape(commenter)}`'
        escaped_issue_or_pull_request = f'`{self.escape(repository)}#{number}`'
        escaped_title = f'`{self.escape(title)}`'
        escaped_body = f'`{self.escape(body)}`'
        converted_url = f'[{self.escape(url)}]({url})'
        await self.send(f'{escaped_commenter} commented on {type} {escaped_issue_or_pull_request}: {escaped_title}\n{escaped_body}\n{converted_url}')

    async def send_pull_request_review(self, sender: str, state: str, repository: str, number: int, title: str, body: str, url: str):
        escaped_sender = f'`@{self.escape(sender)}`'
        escaped_pull_request = f'`{self.escape(repository)}#{number}`'
        escaped_title = f'`{self.escape(title)}`'
        escaped_body = f'`{self.escape(body)}`'
        converted_url = f'[{self.escape(url)}]({url})'
        await self.send(f'{escaped_sender} {state} pull request {escaped_pull_request}: {escaped_title}\n{escaped_body}\n{converted_url}')

    def escape(self, message: str):
        return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', message)
