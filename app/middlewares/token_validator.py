import re
import time
import typing
import jwt

from jwt import PyJWTError
from starlette.requests import Request
from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send
from app.common import consts
from app.utils.date_util import D


class AccessControl:
    def __init__(
        self,
        app: ASGIApp,
        except_path_list: typing.Sequence[str] = None,
        except_path_regex: str = None,
    ) -> None:
        if except_path_list is None:
            except_path_list = ["*"]
        self.app = app
        self.except_path_list = except_path_list
        self.except_path_regex = except_path_regex

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        print(self.except_path_regex)
        print(self.except_path_list)

        request = Request(scope=scope)
        headers = Headers(scope=scope)
        request.state.start = time.time()
        request.state.inspect = None
        request.state.user = None
        request.state.is_admin_access = None
        ip_from = request.headers["x-forwarded-for"] if "x-forwarded-for" in request.headers.keys() else None

        if await self.url_pattern_check(request.url.path, self.except_path_regex) or request.url.path in self.except_path_list:
            return await self.app(scope, receive, send)

        if request.url.path.startswith("/api"):
            # api 인 경우 헤더로 토큰 검사
            if "Authorization" in request.headers.keys():
                request.state.user = await self.token_decode(access_token=request.headers.get("Authorization"))
            else:
                response = JSONResponse(status_code=401, content=dict(msg="AUTHORIZATION_REQUIRED"))
                return await response(scope, receive, send)
        else:
            # 템플릿 렌더링인 경우 쿠키에서 토큰 검사
            print(request.cookies)
            request.cookies["Authorization"] = "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6NiwibmFtZSI6bnVsbCwicGhvbmVfbnVtYmVyIjpudWxsLCJwcm9maWxlX2ltZyI6bnVsbCwic25zX3R5cGUiOm51bGx9._8Lwj9zW5h7q0P7jVLLLzbx2sQzdO1sB9aGJRo2p5XA"

            if "Authorization" not in request.cookies.keys():
                response = JSONResponse(status_code=401, content=dict(msg="AUTHORIZATION_REQUIRED"))
                return await response(scope, receive, send)

            request.state.user = await self.token_decode(access_token=request.cookies.get("Authorization"))

        request.state.req_time = D.datetime()
        print(D.datetime())
        print(D.date())
        print(D.date_num())

        print(request.cookies)
        print(headers)
        res = await self.app(scope, receive, send)
        return res

    @staticmethod
    async def url_pattern_check(path, pattern):
        result = re.match(pattern, path)
        if result:
            return True
        return False

    @staticmethod
    async def token_decode(access_token):
        """
        :param access_token:
        :return:
        """
        try:
            access_token = access_token.replace("Bearer ", "")
            payload = jwt.decode(access_token, key=consts.JWT_SECRET, algorithms=[consts.JWT_ALGORITHM])
        except PyJWTError as e:
            print(e)
            # Raise Error
        return payload
