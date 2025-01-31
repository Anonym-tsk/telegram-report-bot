from aiogram import Bot
from aiogram.types import (
    ChatMemberAdministrator, ChatMemberOwner, ChatMemberBanned, ChatMemberLeft, ChatMemberRestricted,
    BotCommand, BotCommandScopeAllGroupChats
)
from fluent.runtime import FluentLocalization

from bot.config_reader import BotConfig


async def check_bot_rights_main_group(
        bot: Bot,
        bot_config: BotConfig,
):
    for chat_id in bot_config.main_group_id:
        chat_member_info = await bot.get_chat_member(
            chat_id=chat_id, user_id=bot.id
        )
        if not isinstance(chat_member_info, ChatMemberAdministrator):
            raise PermissionError(f"Chat {chat_id}: bot must be an administrator to work properly")
        if not chat_member_info.can_restrict_members or not chat_member_info.can_delete_messages:
            raise PermissionError(f"Chat {chat_id}: bot needs 'ban users' and 'delete messages' permissions to work properly")

async def check_bot_rights_reports_group(
        bot: Bot,
        reports_group_id: int,
):
    chat_member_info = await bot.get_chat_member(
        chat_id=reports_group_id, user_id=bot.id
    )
    if isinstance(chat_member_info, (ChatMemberLeft, ChatMemberBanned)):
        raise PermissionError("bot is banned from the group")
    if isinstance(chat_member_info, ChatMemberRestricted) and not chat_member_info.can_send_messages:
        raise PermissionError("bot is not allowed to send messages")


async def fetch_admins(
        bot: Bot,
        main_group_id: tuple[int, ...],
) -> dict[int, dict[int, object]]:
    result = {}

    for chat_id in main_group_id:
        result[chat_id] = {}
        chat_admins: list[ChatMemberOwner | ChatMemberAdministrator] = await bot.get_chat_administrators(chat_id)
        for admin in chat_admins:
            if admin.user.is_bot:
                continue
            if isinstance(admin, ChatMemberOwner):
                result[chat_id][admin.user.id] = {"can_restrict_members": True}
            else:
                result[chat_id][admin.user.id] = {"can_restrict_members": admin.can_restrict_members}

    return result


async def set_bot_commands(bot: Bot, l10n: FluentLocalization):
    commands = [
        BotCommand(command="report", description=l10n.format_value("bot-command-description")),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeAllGroupChats())
