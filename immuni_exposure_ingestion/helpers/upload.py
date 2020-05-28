#    Copyright (C) 2020 Presidenza del Consiglio dei Ministri.
#    Please refer to the AUTHORS file for more information.
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <https://www.gnu.org/licenses/>.

import asyncio
import random
import re
from functools import wraps
from typing import Any, Awaitable, Callable

from sanic.request import Request
from sanic.response import HTTPResponse

from immuni_common.core.exceptions import SchemaValidationException
from immuni_exposure_ingestion.core import config


def validate_token_format(f: Callable) -> Callable:
    """
    Decorator to ensure that the request Authentication: Bearer Token token is a valid sha256
    string.

    :param f: the decorated function.
    :return: the decorator.
    """

    @wraps(f)
    def _wrapper(request: Request, *args: Any, **kwargs: Any) -> Any:
        if request.token is None or not re.match(r"^[A-Fa-f0-9]{64}$", request.token):
            raise SchemaValidationException()

        return f(request, *args, **kwargs)

    return _wrapper


async def wait_configured_time() -> None:
    """
    Wait for the configured time.
    This is usually useful to make dummy requests last a similar amount of time when compared to the
    real ones, or slow down potential brute force attacks.
    """
    await asyncio.sleep(
        random.normalvariate(
            config.NOISE_REQUEST_TIMEOUT_MILLIS, config.NOISE_REQUEST_TIMEOUT_SIGMA
        )
        / 1000.0
    )


def slow_down_request(f: Callable[..., Awaitable]) -> Callable:
    """
    Decorator to artificially slow down the marked requests, in order to make brute force harder to
    perform.

    :param f: the decorated function.
    :return: the decorator.
    """

    @wraps(f)
    async def _wrapper(*args: Any, **kwargs: Any) -> HTTPResponse:
        await wait_configured_time()
        return await f(*args, **kwargs)

    return _wrapper
