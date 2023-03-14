from typing import Callable

from flask import Request
from telegram import Bot, User

Response = tuple[str, int]
FlaskFunction = Callable[[Request], Response]
TelegramFunction = Callable[[Bot, User], None]

class RequestRouter:
    """
    Routes a request based on its path.
    Provides `route` decorator to imitate Flask-like routing.  
    """
    def __init__(self) -> None:
        self.functions : dict[str, FlaskFunction] = {}

    def route(self, path: str) -> Callable[[FlaskFunction], FlaskFunction]:
        "Associates the callable with the path."
        def register(f: FlaskFunction) -> FlaskFunction:
            self.functions[path] = f
            return f
        return register

    def direct(self, path: str, request: Request) -> Response:
        """
        Routes a request by calling a callable associated with 
        the path in the request. Returns 404 if the path has not
        been associated with a callable. 
        """
        try:
            f = self.functions[path]
        except KeyError:
            return "<H1>Page not found</H1>", 404
        else:
            print(f"Calling {f.__name__} function")
            return f(request)


class CommandRouter:
    """
    Routes commands to a callable.
    Provides `command` decorator.
    """
    def __init__(self) -> None:
        self.functions : dict[str, TelegramFunction] = {}

    def command(self, command: str) -> Callable[[TelegramFunction], TelegramFunction]:
        "Associates the callable with the command."
        def register(f: TelegramFunction) -> TelegramFunction:
            self.functions[command] = f
            return f
        return register

    def direct(self, command: str, bot: Bot, user: User) -> None:
        "Calls a callable associated with the command."
        try:
            f = self.functions[command]
        except KeyError:
            print(f"An unsupported command {command} was called")
            return None
        else:
            print(f"Calling {f.__name__} function")
            return f(bot, user)

    