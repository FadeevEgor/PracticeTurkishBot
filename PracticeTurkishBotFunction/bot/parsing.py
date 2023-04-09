from dataclasses import dataclass
from typing import Any, Optional
from telegram import Bot, User, Update, Message, CallbackQuery  # type: ignore


@dataclass
class UpdateContent:
    user: User
    text: str


@dataclass
class MessageContent(UpdateContent):
    commands: list[str]


@dataclass
class CallbackQueryContent(UpdateContent):
    message_id: int
    query_id: str


def parse_update(update_data: dict[str, Any], bot: Bot) -> Optional[UpdateContent]:
    """
    Parses content of a message from telegram.
    Returns a sender user, cleared from commands text and list of commands.
    """
    print(update_data)
    update = Update.de_json(update_data, bot)

    if update is None:
        print("No update")
        return None

    if update.message is not None:
        return parse_message(update.message, bot)

    if update.callback_query is not None:
        return parse_callback_query(update.callback_query)
    return None


def parse_callback_query(query: CallbackQuery) -> Optional[CallbackQueryContent]:
    if query.data is None:
        print("Ignore: Query without data?")
        return None
    print(f"Callback query: {query.data}")
    return CallbackQueryContent(
        query.from_user,
        query.data,
        query.message.message_id,
        query.id,
    )


def parse_message(message: Message, bot: Bot) -> Optional[MessageContent]:
    if message.from_user is None:
        print("Ignore: No user?")
        return None

    user = message.from_user
    if user.id == bot.id:
        print("Ignore: Message from me?")
        return None

    if message.text is None:
        print("Ignore: No text.")
        return None

    text = message.text
    commands = [text[e.offset : e.offset + e.length] for e in message.entities]
    for command in commands:
        text = text.replace(command, "")
    text = text.strip()
    text = " ".join(text.split())
    return MessageContent(user, text, commands)
