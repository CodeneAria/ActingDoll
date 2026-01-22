"""
Security configuration for WebSocket server
セキュリティ設定
"""
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
            self.allowed_file_dirs = [Path(d.strip()).resolve() for d in allowed_dirs_env.split(':') if d.strip()]
        else:
            # デフォルト: 空（ファイル読み取り無効）
            self.allowed_file_dirs = []
        
        # デフォルトのホスト（localhost）
        self.default_host: str = os.environ.get('WEBSOCKET_HOST', '127.0.0.1')
        
        # デフォルトのポート
        self.default_port: int = int(os.environ.get('WEBSOCKET_PORT', '8765'))
    
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
            abs_path = Path(file_path).resolve()
            
            # ファイルが存在するかチェック
            if not abs_path.exists():
                return False
            
            # 許可されたディレクトリのいずれかのサブディレクトリに含まれているかチェック
            for allowed_dir in self.allowed_file_dirs:
                try:
                    abs_path.relative_to(allowed_dir)
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
