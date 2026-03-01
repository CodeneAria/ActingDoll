"""
Main entry point - Server startup control
"""
import argparse
import asyncio
import logging
import os
from handler_mcp import run_mcp
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
logger = logging.getLogger("AD-MCP")


def _parse_args():
    """
    Parse command line arguments
    """
    parser = argparse.ArgumentParser(
        description='Acting Doll MCP'
    )
    parser.add_argument(
        '-v', '--version', action='version', version=f'%(prog)s {__version__}')
    parser.add_argument(
        '--mode',
        type=str,
        choices=['shttp', 'sse', 'stdin'],
        default='shttp',
        help='Server mode: '
        'shttp(MCP streamable-http), '
        'sse(MCP SSE), '
        'stdin(MCP STDIN)'
    )
    parser.add_argument(
        '--host',
        type=str,
        default=os.environ.get('HOST_ADDRESS', '0.0.0.0'),
        help='Server host (default: environment variable "HOST_ADDRESS" or 0.0.0.0)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=3001,
        help='MCP server port (default: 3001)'
    )
    parser.add_argument(
        '--websocket_url',
        type=str,
        default=f"ws://{os.environ.get('WEBSOCKET_HOST', '127.0.0.1')}:{os.environ.get('WEBSOCKET_PORT', '8765')}",
        help='WebSocket URL for MCP server (default: environment variables "WEBSOCKET_HOST" and "WEBSOCKET_PORT" or 127.0.0.1:8765)'
    )
    return parser.parse_args()


async def _start_acting_doll_mcp():
    """
    Entry point
    """
    try:
        # Parse command line arguments
        args = _parse_args()

        logger.debug(f"Starting Acting Doll MCP Version:{__version__}")

        ##################################################
        # Processing based on mode
        ##################################################
        mcp_task = asyncio.create_task(run_mcp(
            websocket_url=args.websocket_url,
            host=args.host, port=args.port,
            transport=args.mode,
            delay_start=0.0
        ))
        await asyncio.gather(mcp_task)

    except KeyboardInterrupt:
        logger.info("Server stopped")
    except Exception as e:
        logger.error(f"An error occurred while starting the server: {e}")


def main() -> None:
    asyncio.run(_start_acting_doll_mcp())


if __name__ == "__main__":
    main()
