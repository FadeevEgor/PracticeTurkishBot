from typing import Callable, TypeAlias, Any, Coroutine
from telegram import Bot, User  # type: ignore

TelegramCommandFunction: TypeAlias = Callable[[Bot, User], Coroutine[Any, Any, None]]


class BotCommands:
    """
    Routes commands to a callable.
    Provides `command` decorator.
    """

    def __init__(self) -> None:
        self.functions: dict[str, TelegramCommandFunction] = {}

    def command(
        self, command: str
    ) -> Callable[[TelegramCommandFunction], TelegramCommandFunction]:
        "Associates the callable with the command."

        def register(f: TelegramCommandFunction) -> TelegramCommandFunction:
            self.functions[command] = f
            return f

        return register

    async def dispatch(self, command: str, bot: Bot, user: User) -> Any:
        "Calls a callable associated with the command."
        try:
            f = self.functions[command]
        except KeyError:
            print(f"An unsupported command {command} was called")
            return None
        print(f"Calling {f.__name__} function")
        return await f(bot, user)
