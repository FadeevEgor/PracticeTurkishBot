import json
from enum import Enum
from typing import Callable, Sequence, TypeAlias, TypeVar, ParamSpec, Any

from flask import Request, jsonify


Route: TypeAlias = Callable[[dict], Any]


class RequestRouter:
    available_methods = ("GET", "POST", "PUT", "PATCH", "DELETE")
    """Routes a request based on its path and method.
    
    Provides `route` decorator to imitate Flask-like routing.  
    """

    def __init__(self) -> None:
        self.functions: dict[str, dict[str, Route]] = {
            method: {} for method in self.available_methods
        }

    def route(self, path: str, *methods: str) -> Callable[[Route], Route]:
        "Associates the callable with the path and methods."

        def register(f: Route) -> Route:
            for method in methods:
                self.functions[method][path] = f
            return f

        return register

    def dispatch(self, request: Request) -> Any:
        """
        Routes a request by calling a callable associated with
        the path in the request. Returns 404 if the path has not
        been associated with a callable.
        """
        path = request.path
        method = request.method
        try:
            f = self.functions[method][path]
        except KeyError:
            print(f"Dispatch error: {path, method}")
            return "<H1>Page not found</H1>", 404
        else:
            print(f"Calling {f.__name__} function")
            data = json.loads(request.data)
            return jsonify(f(data))
