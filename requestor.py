from typing import Optional
from dataclasses import dataclass

import requests
from fake_useragent import UserAgent


@dataclass
class Requestor:
    """
    Makes requests with headers imitating real browsers  
    """
    user_agent: UserAgent = UserAgent(browsers=["chrome", "edge", "firefox", "safari", "opera"])
    timeout: int = 3

    def generate_header(self) -> dict[str, str]:
        return {"User-Agent": str(self.user_agent.random)}

    def get(self, url: str) -> Optional[requests.Response]:
        try: 
            return requests.get(
            url=url,
            headers=self.generate_header(),
            timeout=self.timeout
        )
        except (requests.TooManyRedirects, requests.HTTPError, requests.Timeout) as msg:
            print(msg)
            return None