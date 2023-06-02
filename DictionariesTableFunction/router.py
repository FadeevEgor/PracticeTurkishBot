import json
from typing import Callable, TypeAlias, Any
from flask import Request, Response, abort


Route: TypeAlias = Callable[[dict], Any]


class RequestRouter:
    available_methods = ("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")
    """Routes a request based on its path and method.
    
    Provides `route` decorator to imitate Flask-like routing.  
    """

    def __init__(self) -> None:
        self.functions: dict[str, dict[str, Route]] = {
            method: {} for method in self.available_methods
        }
    
    def default_headers(self) -> dict[str, str]:
        return {
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "application/json"
        }

    def route(self, path: str, *methods: str, to_json: bool = False) -> Callable[[Route], Route]:
        "Associates the callable with the path and methods."

        def register(f: Route) -> Route:
            for method in methods:
                self.functions[method][path] = (f, to_json)
            return f

        return register

    def dispatch(self, request: Request) -> Response:
        """
        Routes a request by calling a callable associated with
        the path in the request. Returns 404 if the path has not
        been associated with a callable.
        """
        path = request.path
        method = request.method
        try:
            f, to_json = self.functions[method][path]
        except KeyError:
            print(f"Dispatch error: {path, method}")
            return abort(404)
        print(f"Calling {f.__name__} function")
        data = json.loads(request.data)
        response_data = json.dumps(f(data)) if to_json else f(data)
        response = Response(response_data)
        response.status_code = 200
        response.headers.extend(self.default_headers())
        return response