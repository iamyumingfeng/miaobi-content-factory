"""
工具模块

包含通用工具函数。
"""

from .deps import (
    get_token_payload,
    get_token_payload_required,
    get_current_user,
    get_current_super_admin,
    get_current_operator,
    get_current_sub_user,
    get_optional_current_user,
    get_websocket_user,
)
from .pagination import (
    PageParams,
    PaginatedResponse,
    paginate_query,
    create_paginated_response,
)
from .response import (
    ApiResponse,
    success_response,
    error_response,
    ListResponse,
    list_response,
)

__all__ = [
    # deps
    "get_token_payload",
    "get_token_payload_required",
    "get_current_user",
    "get_current_super_admin",
    "get_current_operator",
    "get_current_sub_user",
    "get_optional_current_user",
    "get_websocket_user",
    # pagination
    "PageParams",
    "PaginatedResponse",
    "paginate_query",
    "create_paginated_response",
    # response
    "ApiResponse",
    "success_response",
    "error_response",
    "ListResponse",
    "list_response",
]
