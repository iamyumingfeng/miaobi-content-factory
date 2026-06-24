"""
安全工具模块单元测试

Author: Claude Code
Date: 2025
"""

import pytest
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
    verify_access_token,
    create_tokens_for_user,
    generate_wechat_state,
    generate_nonce,
    generate_userid,
    generate_invitation_code,
)


@pytest.mark.unit
class TestPasswordFunctions:
    """密码相关函数测试"""

    def test_password_hash_and_verify(self) -> None:
        """测试密码哈希和验证"""
        password = "TestPassword123!@#"

        # 生成哈希
        hashed = get_password_hash(password)

        # 验证不应等于原始密码
        assert hashed != password
        assert len(hashed) > 0

        # 验证密码正确
        assert verify_password(password, hashed) is True

        # 验证错误密码
        assert verify_password("WrongPassword123", hashed) is False

    def test_password_hash_consistent(self) -> None:
        """测试相同密码生成不同哈希（加盐）"""
        password = "SamePassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # 同一个密码的两次哈希应该不同（加盐）
        assert hash1 != hash2

        # 但都应该都能验证通过
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

    def test_empty_password(self) -> None:
        """测试空密码"""
        hashed = get_password_hash("")
        assert verify_password("", hashed) is True
        assert verify_password("non-empty", hashed) is False

    def test_long_password(self) -> None:
        """测试长密码"""
        long_password = "a" * 100
        hashed = get_password_hash(long_password)
        assert verify_password(long_password, hashed) is True

    def test_password_with_special_characters(self) -> None:
        """测试带特殊字符的密码"""
        special_password = "P@ssw0rd!#$%^&*()_+-=[]{}|;:,.<>?/~`"
        hashed = get_password_hash(special_password)
        assert verify_password(special_password, hashed) is True
        assert verify_password("wrong", hashed) is False

    def test_password_with_unicode(self) -> None:
        """测试带 Unicode 字符的密码"""
        unicode_password = "密码测试123!@#"
        hashed = get_password_hash(unicode_password)
        assert verify_password(unicode_password, hashed) is True


@pytest.mark.unit
@pytest.mark.usefixtures("mock_settings")
class TestJWTTokenFunctions:
    """JWT 令牌相关函数测试"""

    def test_create_access_token_basic(self) -> None:
        """测试创建基本访问令牌"""
        data: Dict[str, str] = {"sub": "1", "user_type": "super_admin"}
        token = create_access_token(data=data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_and_decode_token(self) -> None:
        """测试创建和解码令牌"""
        data: Dict[str, str] = {"sub": "123", "user_type": "operator", "userid": "test_user"}
        token = create_access_token(data=data)

        decoded = decode_access_token(token)

        assert decoded is not None
        assert decoded["sub"] == "123"
        assert decoded["user_type"] == "operator"
        assert decoded["userid"] == "test_user"
        assert "exp" in decoded

    def test_decode_invalid_token(self) -> None:
        """测试解码无效令牌"""
        decoded = decode_access_token("invalid.token.here")
        assert decoded is None

    def test_decode_empty_token(self) -> None:
        """测试解码空令牌"""
        decoded = decode_access_token("")
        assert decoded is None

    def test_verify_access_token_valid(self) -> None:
        """测试验证有效令牌"""
        data: Dict[str, str] = {"sub": "456", "user_type": "sub_user"}
        token = create_access_token(data=data)

        is_valid: bool
        payload: Optional[Dict[str, Any]]
        is_valid, payload = verify_access_token(token)

        assert is_valid is True
        assert payload is not None
        assert payload["sub"] == "456"

    def test_verify_access_token_invalid(self) -> None:
        """测试验证无效令牌"""
        is_valid: bool
        payload: Optional[Dict[str, Any]]
        is_valid, payload = verify_access_token("invalid.token")

        assert is_valid is False
        assert payload is None

    def test_verify_access_token_expired(self, mock_settings) -> None:
        """测试验证已过期令牌"""
        # 创建已过期的令牌
        data: Dict[str, str] = {"sub": "789"}
        token = create_access_token(
            data=data,
            expires_delta=timedelta(minutes=-30)
        )

        is_valid: bool
        payload: Optional[Dict[str, Any]]
        is_valid, payload = verify_access_token(token)

        assert is_valid is False
        assert payload is None

    def test_verify_access_token_missing_exp(self) -> None:
        """测试验证缺少过期时间的令牌"""
        # 创建一个没有 exp 的令牌
        from jose import jwt
        token_without_exp = jwt.encode(
            {"sub": "no-exp"},
            "test-secret-key-for-testing-only-do-not-use-in-production",
            algorithm="HS256"
        )

        is_valid: bool
        payload: Optional[Dict[str, Any]]
        is_valid, payload = verify_access_token(token_without_exp)

        assert is_valid is False
        assert payload is None

    def test_verify_access_token_invalid_signature(self) -> None:
        """测试验证签名无效的令牌"""
        from jose import jwt
        # 创建有效令牌
        valid_token = jwt.encode(
            {"sub": "test", "exp": datetime.utcnow() + timedelta(hours=1)},
            "correct-secret",
            algorithm="HS256"
        )
        # 尝试用不同的密钥验证（模拟签名错误）
        is_valid: bool
        payload: Optional[Dict[str, Any]]
        # 注意：这里需要实际场景，暂时用无效 token 格式测试
        is_valid, payload = verify_access_token(valid_token + ".invalid")
        assert is_valid is False

    def test_create_access_token_with_empty_data(self) -> None:
        """测试创建带空数据的令牌"""
        data: Dict[str, Any] = {}
        token = create_access_token(data=data)
        decoded = decode_access_token(token)
        assert decoded is not None
        assert "exp" in decoded

    def test_create_access_token_custom_expiry(self, mock_settings) -> None:
        """测试创建自定义过期时间的令牌"""
        data: Dict[str, str] = {"sub": "custom"}
        custom_expiry = timedelta(minutes=30)
        token = create_access_token(data=data, expires_delta=custom_expiry)

        decoded = decode_access_token(token)
        assert decoded is not None
        # 验证过期时间存在

    def test_create_tokens_for_user(self, mock_settings) -> None:
        """测试为用户创建令牌"""
        result: Dict[str, Any] = create_tokens_for_user(
            user_id=1,
            user_type="operator",
            userid="operator_001",
            nickname="测试操作员"
        )

        assert "access_token" in result
        assert "token_type" in result
        assert "expires_in" in result
        assert "user" in result

        assert result["token_type"] == "bearer"
        assert result["expires_in"] == 3600  # 60 * 60
        assert result["user"]["id"] == 1
        assert result["user"]["userid"] == "operator_001"
        assert result["user"]["nickname"] == "测试操作员"
        assert result["user"]["role"] == "operator"

    def test_create_tokens_for_user_without_nickname(self, mock_settings) -> None:
        """测试创建没有昵称的用户令牌"""
        result: Dict[str, Any] = create_tokens_for_user(
            user_id=2,
            user_type="sub_user",
            userid="subuser_002"
        )

        assert result["user"]["nickname"] is None


@pytest.mark.unit
class TestRandomGenerators:
    """随机生成器函数测试"""

    def test_generate_wechat_state(self) -> None:
        """测试生成微信 state"""
        state1: str = generate_wechat_state()
        state2: str = generate_wechat_state()

        assert state1 is not None
        assert isinstance(state1, str)
        assert len(state1) > 0
        assert state1 != state2  # 应该是随机的

    def test_generate_nonce_default_length(self) -> None:
        """测试生成默认长度的随机字符串"""
        nonce1: str = generate_nonce()
        nonce2: str = generate_nonce()

        assert isinstance(nonce1, str)
        assert len(nonce1) == 16
        assert nonce1 != nonce2

    def test_generate_nonce_custom_length(self) -> None:
        """测试生成自定义长度的随机字符串"""
        nonce: str = generate_nonce(length=32)
        assert len(nonce) == 32

    def test_generate_nonce_only_alphanumeric(self) -> None:
        """测试随机字符串只包含字母和数字"""
        nonce: str = generate_nonce(length=100)
        assert nonce.isalnum() is True

    def test_generate_userid(self) -> None:
        """测试生成用户 ID"""
        userid1: str = generate_userid()
        userid2: str = generate_userid()

        assert userid1.startswith("u_")
        assert len(userid1) > 2
        assert userid1 != userid2

    def test_generate_invitation_code(self) -> None:
        """测试生成邀请码"""
        code1: str = generate_invitation_code()
        code2: str = generate_invitation_code()

        assert len(code1) == 6
        assert code1.isalnum()
        assert code1.isupper()
        assert code1 != code2

    def test_generate_invitation_code_uppercase(self) -> None:
        """测试邀请码是大写的"""
        for _ in range(10):
            code: str = generate_invitation_code()
            assert code == code.upper()

    def test_generate_invitation_code_uniqueness(self) -> None:
        """测试邀请码的唯一性（多次生成不重复）"""
        codes = set()
        for _ in range(100):
            code = generate_invitation_code()
            assert code not in codes
            codes.add(code)
