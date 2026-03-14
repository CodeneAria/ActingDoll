"""
Main entry point - Server startup control
"""
import argparse
import asyncio
import logging
import os
from modules.handler_cubism_controller import run_websocket
from modules.security_config import SecurityConfig
try:
    from importlib.metadata import version as get_version
    __version__ = get_version('acting-doll-server')
except Exception:
    __version__ = '--,--,--'


str_format = '[%(asctime)s] %(levelname)s\t[%(name)s]\t%(message)s'
# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format=str_format
)
logger = logging.getLogger("AD-Server")


def _parse_args():
    """
    Parse command line arguments
    """
    parser = argparse.ArgumentParser(
        description='Live2D model control Server with MCP'
    )
    parser.add_argument('-v', '--version', action='version',
                        version=f'%(prog)s {__version__}')
    parser.add_argument(
        '--model-dir',
        type=str,
        default=os.environ.get('CUBISM_MODEL_DIR', 'src/Cubism/Resources'),
        help='Path to model directory (default: src/Cubism/Resources, environment variable: CUBISM_MODEL_DIR)'
    )
    parser.add_argument(
        '--host',
        type=str,
        default=os.environ.get('WEBSOCKET_HOST', '127.0.0.1'),
        help='Server host (default: environment variable "WEBSOCKET_HOST" or 127.0.0.1)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=int(os.environ.get('WEBSOCKET_PORT', 8765)),
        help='Server port (default: environment variable "WEBSOCKET_PORT" or 8765)'
    )
    parser.add_argument(
        '--tts_url',
        type=str,
        default=os.environ.get('TTS_URL', 'http://localhost:50021'),
        help='TTS server URL (default: environment variable "TTS_URL" or http://localhost:50021)'
    )
    parser.add_argument(
        '--tts_model_info',
        type=str,
        default=os.environ.get('TTS_MODEL_INFO', ''),
        help='TTS model information (default: environment variable "TTS_MODEL_INFO" or empty)'
    )
    parser.add_argument(
        '--console',
        action='store_true',
        help='Enable interactive console'
    )
    parser.add_argument(
        '--disable-auth',
        action='store_true',
        help='Disable authentication (note security risks)'
    )
    return parser.parse_args()


async def _start_acting_doll_server():
    """
    Entry point
    """
    try:
        # Parse command line arguments
        args = _parse_args()

        logger.debug(f"Starting Acting Doll Server Version:{__version__}")

        # Initialize security configuration
        security_config = SecurityConfig()

        # Set host and port
        host = args.host if args.host is not None else security_config.default_host
        port = args.port if args.port is not None else security_config.default_port

        # tts_url = f"http://{host}:{args.tts_port}"  # TTSサーバーのURLを指定
        tts_url = args.tts_url  # TTSサーバーのURLを指定
        model_name = ""
        model_type = ""

        ##################################################
        # Processing based on mode
        ##################################################
        # Cubism mode
        cubism_task = asyncio.create_task(run_websocket(
            host=host, port=port,
            tts_url=tts_url,
            model_name=model_name,
            model_type=model_type,
            security_config=security_config,
            model_dir=args.model_dir,
            console=args.console,
            disable_auth=args.disable_auth
        ))

        await asyncio.gather(cubism_task)

    except KeyboardInterrupt:
        logger.info("Server stopped")
    except Exception as e:
        logger.error(f"An error occurred while starting the server: {e}")


def main() -> None:
    asyncio.run(_start_acting_doll_server())


if __name__ == "__main__":
    main()
