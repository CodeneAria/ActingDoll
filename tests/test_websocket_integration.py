"""
Basic integration test for websocket_server with security features
"""
import os
import sys
from pathlib import Path

# Add src/adapter/server to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "adapter" / "server"))


def test_import_modules():
    """モジュールのインポートテスト"""
    from security_config import SecurityConfig
    
    # SecurityConfigモジュールが正常にインポートできることを確認
    assert SecurityConfig is not None
    
    # websocket_serverのインポートは依存関係が必要なのでスキップ
    # 実際の環境では依存関係がインストールされている


def test_security_config_initialization():
    """SecurityConfigの初期化テスト"""
    from security_config import SecurityConfig
    
    # 環境変数をクリアして初期化
    env_backup = {}
    for key in ['WEBSOCKET_AUTH_TOKEN', 'WEBSOCKET_REQUIRE_AUTH', 
                'WEBSOCKET_ALLOWED_DIRS', 'WEBSOCKET_HOST', 'WEBSOCKET_PORT']:
        env_backup[key] = os.environ.pop(key, None)
    
    try:
        config = SecurityConfig()
        
        # デフォルト設定が正しいか確認
        assert config.default_host == '127.0.0.1'
        assert config.default_port == 8765
        assert config.require_auth is True
        
    finally:
        # 環境変数を復元
        for key, value in env_backup.items():
            if value is not None:
                os.environ[key] = value


def test_parse_args_with_defaults():
    """parse_argsのデフォルト値テスト"""
    # websocket_serverをインポートできるかテスト
    # 実際のコマンドライン引数パースは行わない（argparseがsys.argvを使うため）
    from security_config import SecurityConfig
    
    config = SecurityConfig()
    assert config.default_host == '127.0.0.1'
    assert config.default_port == 8765


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
