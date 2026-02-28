"""
Tests for security_config module
"""
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add src/adapter/server to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent /
                "src" / "adapter" / "server"))

from security_config import SecurityConfig


class TestSecurityConfig:
    """SecurityConfigクラスのテスト"""

    def test_default_config(self):
        """デフォルト設定のテスト"""
        # 環境変数をクリア
        env_backup = {}
        for key in ['WEBSOCKET_AUTH_TOKEN', 'WEBSOCKET_REQUIRE_AUTH',
                    'WEBSOCKET_ALLOWED_DIRS', 'WEBSOCKET_HOST', 'WEBSOCKET_PORT']:
            env_backup[key] = os.environ.pop(key, None)

        try:
            config = SecurityConfig()

            # デフォルトは認証必須
            assert config.require_auth is True
            # トークンは未設定
            assert config.auth_token is None
            # ホワイトリストは空
            assert config.allowed_file_dirs == []
            # デフォルトホストは127.0.0.1
            assert config.default_host == '127.0.0.1'
            # デフォルトポートは8765
            assert config.default_port == 8765
        finally:
            # 環境変数を復元
            for key, value in env_backup.items():
                if value is not None:
                    os.environ[key] = value

    def test_auth_token_from_env(self):
        """環境変数から認証トークンを読み込むテスト"""
        os.environ['WEBSOCKET_AUTH_TOKEN'] = 'test-token-123'
        try:
            config = SecurityConfig()
            assert config.auth_token == 'test-token-123'
        finally:
            os.environ.pop('WEBSOCKET_AUTH_TOKEN', None)

    def test_require_auth_false(self):
        """認証を無効にするテスト"""
        os.environ['WEBSOCKET_REQUIRE_AUTH'] = 'false'
        try:
            config = SecurityConfig()
            assert config.require_auth is False
        finally:
            os.environ.pop('WEBSOCKET_REQUIRE_AUTH', None)

    def test_allowed_dirs_from_env(self):
        """環境変数からホワイトリストを読み込むテスト"""
        with tempfile.TemporaryDirectory() as tmpdir1:
            with tempfile.TemporaryDirectory() as tmpdir2:
                os.environ['WEBSOCKET_ALLOWED_DIRS'] = f'{tmpdir1}:{tmpdir2}'
                try:
                    config = SecurityConfig()
                    assert len(config.allowed_file_dirs) == 2
                    assert Path(tmpdir1).resolve() in config.allowed_file_dirs
                    assert Path(tmpdir2).resolve() in config.allowed_file_dirs
                finally:
                    os.environ.pop('WEBSOCKET_ALLOWED_DIRS', None)

    def test_is_file_allowed_empty_whitelist(self):
        """ホワイトリストが空の場合のファイルアクセステスト"""
        config = SecurityConfig()
        assert config.allowed_file_dirs == []

        with tempfile.NamedTemporaryFile() as tmpfile:
            # ホワイトリストが空の場合は全て拒否
            assert config.is_file_allowed(tmpfile.name) is False

    def test_is_file_allowed_with_whitelist(self):
        """ホワイトリストありの場合のファイルアクセステスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # テスト用ファイルを作成
            allowed_file = Path(tmpdir) / "allowed.txt"
            allowed_file.write_text("test")

            # 別のディレクトリを作成
            with tempfile.TemporaryDirectory() as tmpdir2:
                denied_file = Path(tmpdir2) / "denied.txt"
                denied_file.write_text("test")

                # ホワイトリストを設定
                os.environ['WEBSOCKET_ALLOWED_DIRS'] = tmpdir
                try:
                    config = SecurityConfig()

                    # 許可されたディレクトリ内のファイルはOK
                    assert config.is_file_allowed(str(allowed_file)) is True

                    # 許可されていないディレクトリ内のファイルはNG
                    assert config.is_file_allowed(str(denied_file)) is False

                    # 存在しないファイルはNG
                    assert config.is_file_allowed(str(Path(tmpdir) / "nonexistent.txt")) is False
                finally:
                    os.environ.pop('WEBSOCKET_ALLOWED_DIRS', None)

    def test_is_file_allowed_subdirectory(self):
        """サブディレクトリ内のファイルアクセステスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # サブディレクトリとファイルを作成
            subdir = Path(tmpdir) / "subdir" / "nested"
            subdir.mkdir(parents=True)
            test_file = subdir / "test.txt"
            test_file.write_text("test")

            # 親ディレクトリをホワイトリストに追加
            os.environ['WEBSOCKET_ALLOWED_DIRS'] = tmpdir
            try:
                config = SecurityConfig()

                # サブディレクトリ内のファイルもOK
                assert config.is_file_allowed(str(test_file)) is True
            finally:
                os.environ.pop('WEBSOCKET_ALLOWED_DIRS', None)

    def test_validate_auth_token_no_auth_required(self):
        """認証不要の場合のトークン検証テスト"""
        os.environ['WEBSOCKET_REQUIRE_AUTH'] = 'false'
        try:
            config = SecurityConfig()

            # 認証が無効なら常にTrue
            assert config.validate_auth_token(None) is True
            assert config.validate_auth_token("any-token") is True
        finally:
            os.environ.pop('WEBSOCKET_REQUIRE_AUTH', None)

    def test_validate_auth_token_with_auth(self):
        """認証ありの場合のトークン検証テスト"""
        os.environ['WEBSOCKET_AUTH_TOKEN'] = 'correct-token'
        try:
            config = SecurityConfig()

            # 正しいトークンはOK
            assert config.validate_auth_token('correct-token') is True

            # 間違ったトークンはNG
            assert config.validate_auth_token('wrong-token') is False
            assert config.validate_auth_token(None) is False
        finally:
            os.environ.pop('WEBSOCKET_AUTH_TOKEN', None)

    def test_validate_auth_token_no_token_set(self):
        """認証トークンが設定されていない場合のテスト"""
        # 認証必須だがトークンが設定されていない場合
        env_backup = {}
        for key in ['WEBSOCKET_AUTH_TOKEN', 'WEBSOCKET_REQUIRE_AUTH']:
            env_backup[key] = os.environ.pop(key, None)

        try:
            # 認証必須にするが、トークンは設定しない
            os.environ['WEBSOCKET_REQUIRE_AUTH'] = 'true'
            config = SecurityConfig()

            # トークンが設定されていないので全て拒否
            assert config.validate_auth_token('any-token') is False
            assert config.validate_auth_token(None) is False
        finally:
            # 環境変数を復元
            for key, value in env_backup.items():
                if value is not None:
                    os.environ[key] = value
                else:
                    os.environ.pop(key, None)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
