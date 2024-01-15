from telegram import ChatMember, ChatMemberUpdated, Update
from telegram.ext import Application, ContextTypes, ChatJoinRequestHandler, ChatMemberHandler
from typing import Optional, Tuple
from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv('TOKEN')
CHANNEL_ID1 = os.getenv('CHANNEL_ID1')
CHANNEL_ID2 = os.getenv('CHANNEL_ID2')

UNSUB_MSG = os.getenv('UNSUB_MSG')
APPROVE_MSG = os.getenv('APPROVE_MSG')


def extract_status_change(chat_member_update: ChatMemberUpdated) -> Optional[Tuple[bool, bool]]:
    # Takes a ChatMemberUpdated instance and extracts whether the 'old_chat_member' was a member
    # of the chat and whether the 'new_chat_member' is a member of the chat. Returns None, if
    # the status didn't change.

    status_change = chat_member_update.difference().get("status")
    old_is_member, new_is_member = chat_member_update.difference().get("is_member",
                                                                       (None, None))

    if status_change is None:
        return None

    old_status, new_status = status_change
    was_member = old_status in [
        ChatMember.MEMBER,
        ChatMember.OWNER,
        ChatMember.ADMINISTRATOR,
    ] or (old_status == ChatMember.RESTRICTED and old_is_member is True)
    is_member = new_status in [
        ChatMember.MEMBER,
        ChatMember.OWNER,
        ChatMember.ADMINISTRATOR,
    ] or (new_status == ChatMember.RESTRICTED and new_is_member is True)

    return was_member, is_member


async def accept_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    subscriptions = await context.bot.get_chat_member(chat_id=CHANNEL_ID1, user_id=user_id)

    if subscriptions.status == 'left':
        await context.bot.send_message(user_id, UNSUB_MSG)
    else:
        await context.bot.approve_chat_join_request(chat_id=update.effective_chat.id, user_id=user_id)
        await context.bot.send_message(user_id, APPROVE_MSG)


async def checker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result = extract_status_change(update.chat_member)
    if result is None:
        return

    user_id = update.chat_member.from_user.id
    was_member, is_member = result

    subscriptions1 = await context.bot.get_chat_member(chat_id=CHANNEL_ID1, user_id=user_id)
    subscriptions2 = await context.bot.get_chat_member(chat_id=CHANNEL_ID2, user_id=user_id)

    if was_member and not is_member:
        if subscriptions1.status == 'member' and subscriptions2.status == 'member':
            return None
        elif subscriptions1.status == 'left' and subscriptions2.status == 'member':
            await context.bot.ban_chat_member(chat_id=CHANNEL_ID2, user_id=user_id)
            await context.bot.unban_chat_member(chat_id=CHANNEL_ID2, user_id=user_id, only_if_banned=True)
            await context.bot.send_message(update.effective_user.id, UNSUB_MSG)


def main() -> None:
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(ChatJoinRequestHandler(accept_join_request))
    application.add_handler(ChatMemberHandler(
        checker, ChatMemberHandler.CHAT_MEMBER))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
