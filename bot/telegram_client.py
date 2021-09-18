import aiogram
import asyncio
import logging
import traceback
import typing
import re


class TelegramClient:

    def __init__(self, chat_id_discussions: str, chat_id_pushes: str, *args, **kwargs):
        self.chat_id_discussions = chat_id_discussions
        self.chat_id_pushes = chat_id_pushes
        self.logger = logging.getLogger('TelegramClient')
        self.bot = aiogram.Bot(*args, **kwargs)
        self.message_queue = asyncio.Queue()
        self.shutdown_event = asyncio.Event()

    async def __aenter__(self) -> 'TelegramClient':
        self.send_task = asyncio.create_task(self.send_runner())
        return self

    async def __aexit__(self, *args, **kwargs):
        self.shutdown_event.set()
        await self.send_task
        if not self.message_queue.empty():
            self.logger.error(f'{self.message_queue.qsize()} unsent messages:')
        while True:
            try:
                chat_id, message, message_kwargs = self.message_queue.get_nowait()
                self.logger.error(f'Message \'{message}\' to chat {chat_id} with kwargs={message_kwargs}')
            except asyncio.QueueEmpty:
                break
        await self.bot.close()

    async def send_runner(self):
        while True:
            got_shutdown = self.shutdown_event.wait()
            got_message = self.discussion_message_queue.get()
            done, _ = await asyncio.wait((got_shutdown, got_message), return_when=asyncio.FIRST_COMPLETED)
            if got_shutdown in done:
                break
            assert got_message in done
            chat_id, message, message_kwargs = await got_message
            back_off_timeout = 6
            while True:
                try:
                    await self.bot.send_message(chat_id=chat_id, text=message, parse_mode='MarkdownV2', disable_web_page_preview=True, **message_kwargs)
                except Exception:
                    self.logger.error(f'Failed to send message \'{message}\' to chat {chat_id} with kwargs={message_kwargs}')
                    traceback.print_exc()
                    self.logger.error(f'Sleeping for {back_off_timeout} seconds...')
                    await asyncio.sleep(back_off_timeout)
                    if back_off_timeout <= 120:
                        back_off_timeout *= 2
                    self.logger.error(f'Retrying...')

    async def send_to_discussions(self, message: str, **kwargs):
        await self.message_queue.put((self.chat_id_discussions, message, kwargs))

    async def send_to_pushes(self, message: str, **kwargs):
        await self.message_queue.put((self.chat_id_pushes, message, kwargs))

    async def send_startup(self):
        await self.send_to_discussions('\U0001f92b Online again', disable_notification=True)
        await self.send_to_pushes('\U0001f92b Online again', disable_notification=True)

    async def send_unauthorized_request(self, remote: str):
        await self.send_to_pushes(f'\U000026a0 Unauthorized request from `{self.escape(remote)}`', disable_notification=True)

    async def send_create_webhook_of_repository(self, fork_owner: str, fork_repo: str):
        await self.send_to_pushes(f'\U00002705 Creating webhook at `{self.escape(fork_owner)}/{self.escape(fork_repo)}`\\.\\.\\.', disable_notification=True)

    async def send_create_webhook_of_organization(self, organization: str):
        await self.send_to_pushes(f'\U00002705 Creating webhook at `{self.escape(organization)}`\\.\\.\\.', disable_notification=True)

    async def send_push(self, pusher: str, commit_messages: typing.List[str], commits_url: str, branch: str, branch_url: str, repository: str, repository_url: str, is_forced: bool):
        escaped_pusher = f'`@{self.escape(pusher)}`'
        escaped_commit_messages = '\n'.join(
            [f'\\- `{self.escape(message)}`' for message in commit_messages[-10:]],
        )
        if len(commit_messages) > 10:
            escaped_commit_messages = f'\\.\\.\\. {len(commit_messages) - 10} more\n' + \
                escaped_commit_messages
        commit_label = 'commits' if len(commit_messages) > 1 else 'commit'
        converted_commits_url = f'[{len(commit_messages)} {commit_label}]({commits_url})'
        converted_branch_url = f'[{self.escape(branch)}]({branch_url})'
        converted_repository_url = f'[{self.escape(repository)}]({repository_url})'
        force_label = 'force ' if is_forced else ''
        await self.send_to_pushes(f'{escaped_pusher} {force_label}pushed {converted_commits_url} to {converted_branch_url} at {converted_repository_url}:\n\n{escaped_commit_messages}')

    async def send_issue_or_pull_request(self, sender: str, type: str, action: str, repository: str, number: int, title: str, url: str):
        escaped_sender = f'`@{self.escape(sender)}`'
        escaped_action = self.escape(action)
        escaped_title = f'`{self.escape(title)}`'
        converted_url = f'[{self.escape(repository)}\\#{number}]({url})'
        await self.send_to_discussions(f'{escaped_sender} {escaped_action} {type} {escaped_title} \\({converted_url}\\)')
        # TODO: merge

    async def send_issue_or_pull_request_comment(self, commenter: str, type: str, repository: str, number: int, title: str, body: str, comment_url: str, url: str):
        escaped_commenter = f'`@{self.escape(commenter)}`'
        escaped_title = f'`{self.escape(title)}`'
        escaped_body = f':\n\n`{self.escape(body.strip())}`' if len(
            body.strip()) > 0 else ''
        converted_url = f'[{self.escape(repository)}\\#{number}]({url})'
        await self.send_to_discussions(f'{escaped_commenter} [commented on {type}]({comment_url}) {escaped_title} \\({converted_url}\\){escaped_body}')

    async def send_pull_request_review(self, sender: str, state: str, repository: str, number: int, title: str, body: str, comment_url: str, url: str):
        escaped_sender = f'`@{self.escape(sender)}`'
        escaped_title = f'`{self.escape(title)}`'
        escaped_body = f':\n\n`{self.escape(body.strip())}`' if len(
            body.strip()) > 0 else ''
        converted_url = f'[{self.escape(repository)}\\#{number}]({url})'
        await self.send_to_discussions(f'{escaped_sender} [{state} pull request]({comment_url}) {escaped_title} \\({converted_url}\\){escaped_body}')

    def escape(self, message: str):
        return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', message)
