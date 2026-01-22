"""
Security configuration for WebSocket server
セキュリティ設定
"""
import logging
import os
from pathlib import Path
from typing import Optional


class SecurityConfig:
    """WebSocketサーバーのセキュリティ設定"""
    
    def __init__(self):
        # 認証トークン（環境変数から取得）
        self.auth_token: Optional[str] = os.environ.get('WEBSOCKET_AUTH_TOKEN')
        
        # 認証を必須とするかどうか（デフォルト: True）
        self.require_auth: bool = os.environ.get('WEBSOCKET_REQUIRE_AUTH', 'true').lower() == 'true'
        
        # 許可されたファイルディレクトリ（ホワイトリスト）
        allowed_dirs_env = os.environ.get('WEBSOCKET_ALLOWED_DIRS', '')
        if allowed_dirs_env:
            self.allowed_file_dirs = []
            for d in allowed_dirs_env.split(':'):
                if d.strip():
                    try:
                        # strict=Trueでシンボリックリンクをチェック
                        resolved_path = Path(d.strip()).resolve(strict=False)
                        self.allowed_file_dirs.append(resolved_path)
                    except Exception as e:
                        logger = logging.getLogger(__name__)
                        logger.warning(f"ホワイトリストのディレクトリ '{d}' の解決に失敗: {e}")
        else:
            # デフォルト: 空（ファイル読み取り無効）
            self.allowed_file_dirs = []
        
        # デフォルトのホスト（localhost）
        self.default_host: str = os.environ.get('WEBSOCKET_HOST', '127.0.0.1')
        
        # デフォルトのポート（検証あり）
        try:
            port = int(os.environ.get('WEBSOCKET_PORT', '8765'))
            if not (1 <= port <= 65535):
                logger = logging.getLogger(__name__)
                logger.warning(f"無効なポート番号 {port}。デフォルト 8765 を使用します。")
                port = 8765
            self.default_port: int = port
        except ValueError:
            logger = logging.getLogger(__name__)
            logger.warning(f"無効なポート番号 '{os.environ.get('WEBSOCKET_PORT')}'。デフォルト 8765 を使用します。")
            self.default_port: int = 8765
    
    def is_file_allowed(self, file_path: str) -> bool:
        """
        ファイルパスがホワイトリストに含まれているかチェック
        
        Args:
            file_path: チェックするファイルパス
            
        Returns:
            許可されている場合True、それ以外False
        """
        if not self.allowed_file_dirs:
            # ホワイトリストが空の場合は全て拒否
            return False
        
        try:
            # 絶対パスに変換して正規化
            abs_path = Path(file_path).resolve(strict=False)
            
            # ファイルが存在するかチェック
            if not abs_path.exists():
                return False
            
            # シンボリックリンクの場合、実際のパスを取得
            if abs_path.is_symlink():
                real_path = abs_path.resolve(strict=True)
            else:
                real_path = abs_path
            
            # 許可されたディレクトリのいずれかのサブディレクトリに含まれているかチェック
            for allowed_dir in self.allowed_file_dirs:
                try:
                    # 実際のパスが許可されたディレクトリ内にあるかチェック
                    real_path.relative_to(allowed_dir)
                    return True
                except ValueError:
                    continue
            
            return False
        except Exception:
            return False
    
    def validate_auth_token(self, token: Optional[str]) -> bool:
        """
        認証トークンを検証
        
        Args:
            token: 検証するトークン
            
        Returns:
            認証成功の場合True、それ以外False
        """
        # 認証が無効の場合は常に成功
        if not self.require_auth:
            return True
        
        # 認証が必須だがトークンが設定されていない場合は拒否
        if not self.auth_token:
            return False
        
        # トークンを比較
        return token == self.auth_token
