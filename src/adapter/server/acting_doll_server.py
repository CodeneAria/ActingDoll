"""
メインエントリーポイント - サーバー起動制御
"""
import argparse
import asyncio
import logging
import os
from handler_cubism_controller import run_websocket
from handler_mcp import run_mcp
from security_config import SecurityConfig
from typing import Optional
try:
    from importlib.metadata import version as get_version
    __version__ = get_version('acting-doll-server')
except Exception:
    __version__ = '--,--,--'

# グローバルなタスク（後で初期化）
mcp_task: Optional[asyncio.Task] = None
cubism_task: Optional[asyncio.Task] = None


str_format = '[%(asctime)s] %(levelname)s\t[%(name)s]\t%(message)s'
# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format=str_format
)
logger = logging.getLogger("ActingDoll")


def _parse_args():
    """
    コマンドライン引数をパース
    """
    parser = argparse.ArgumentParser(
        description='Live2D model control Server with MCP'
    )
    parser.add_argument('-v', '--version', action='version',
                        version=f'%(prog)s {__version__}')
    parser.add_argument(
        '--mode_mcp',
        type=str,
        choices=['shttp', 'sse', 'stdin', 'none'],
        default='shttp',
        help='サーバーモード: '
        'shttp(MCP streamable-http), '
        'sse(MCP SSE), '
        'stdin(MCP STDIN), '
        'none(サーバー起動なし)'
    )
    parser.add_argument(
        '--mode_stop_cubism',
        action='store_true',
        default=False,
        help='CubismControllerを起動しないフラグ（指定しない場合は起動します）'
    )
    parser.add_argument(
        '--model-dir',
        type=str,
        default=os.environ.get('CUBISM_MODEL_DIR', 'src/Cubism/Resources'),
        help='モデルディレクトリのパス (デフォルト: src/Cubism/Resources, 環境変数: CUBISM_MODEL_DIR)'
    )
    parser.add_argument(
        '--host',
        type=str,
        default=os.environ.get('WEBSOCKET_HOST', '127.0.0.1'),
        help='サーバーのホスト (デフォルト: 環境変数"WEBSOCKET_HOST"または127.0.0.1)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=int(os.environ.get('WEBSOCKET_PORT', 8765)),
        help='サーバーのポート (デフォルト: 環境変数"WEBSOCKET_PORT"または8765)'
    )
    parser.add_argument(
        '--mcp-port',
        type=int,
        default=3001,
        help='MCPサーバーのポート (デフォルト: 3001)'
    )
    parser.add_argument(
        '--console',
        action='store_true',
        help='対話型コンソールを有効化'
    )
    parser.add_argument(
        '--disable-auth',
        action='store_true',
        help='認証を無効化（セキュリティリスクに注意）'
    )
    return parser.parse_args()


async def _run_acting_doll():
    """
    エントリーポイント
    """
    global mcp_task, cubism_task
    try:
        # コマンドライン引数をパース
        args = _parse_args()

        logger.debug(f"Acting Doll Server Version:{__version__} を起動")

        # セキュリティ設定を初期化
        security_config = SecurityConfig()

        # ホストとポートの設定
        host = args.host if args.host is not None else security_config.default_host
        port = args.port if args.port is not None else security_config.default_port

        # Cubism ControllerのURL
        websocket_url = f"ws://{host}:{port}"

        ##################################################
        # モードに応じた処理
        ##################################################
        # MCPモード
        if args.mode_mcp == 'sse' or args.mode_mcp == 'shttp' or args.mode_mcp == 'stdin':
            mcp_task = asyncio.create_task(run_mcp(
                websocket_url=websocket_url,
                host=host, port=args.mcp_port,
                transport=args.mode_mcp,
                delay_start=0.5 if not args.mode_stop_cubism else 0.0
            ))

        # cubismモード
        if not args.mode_stop_cubism:
            from handler_mcp import stop_mcp_server
            cubism_task = asyncio.create_task(run_websocket(
                host=host, port=port,
                security_config=security_config,
                stop_mcp_server=stop_mcp_server,
                model_dir=args.model_dir,
                console=args.console if args.mode_mcp != 'none' else False,
                disable_auth=args.disable_auth
            ))

        if (mcp_task is not None) and (cubism_task is not None):
            await asyncio.gather(cubism_task, mcp_task)
        elif cubism_task is not None:
            await asyncio.gather(cubism_task)
        elif mcp_task is not None:
            await asyncio.gather(mcp_task)
        else:
            logger.error("有効なサーバーモードが指定されていません")
        return

    except KeyboardInterrupt:
        logger.info("サーバーを停止しました")
    except Exception as e:
        logger.error(f"サーバーの起動中にエラーが発生しました: {e}")


def run_acting_doll():
    asyncio.run(_run_acting_doll())


if __name__ == "__main__":
    run_acting_doll()
