#!/usr/bin/env python3
"""
Docker container run script for Cubism SDK Web
"""

import argparse
import os
import subprocess
import sys
import yaml
import logging
from pathlib import Path

str_format = '[%(levelname)s]\t%(message)s'
# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format=str_format
)
logger = logging.getLogger(__name__)


def run_command(cmd, shell=True, capture_output=False, check=False):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            capture_output=capture_output,
            text=True,
            check=check
        )
        return result
    except subprocess.CalledProcessError as e:
        if check:
            raise
        return e


def main(work_dir, config_path, is_production=False, is_mcp=False):
    # Load settings from YAML
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)

    DOCKER_IMAGE_NAME = config['docker']['image']['name']
    DOCKER_IMAGE_VER = config['docker']['image']['version']
    DOCKER_CONTAINER_NAME = config['docker']['container']['name']

    acting_doll_node = f"/root/workspace/adapter/acting_doll"
    mcp_node = f"/root/workspace/adapter/server"

    # Show running containers
    logger.info("[Build model inside Cubism SDK for Web container]")
    ps_filter_cmd = (
        f'docker ps -a --filter "ancestor={DOCKER_IMAGE_NAME}:{DOCKER_IMAGE_VER}" '
        f'--format "table {{{{.ID}}}}\\t{{{{.Image}}}}\\t{{{{.Status}}}}\\t{{{{.Names}}}}\\t{{{{.Ports}}}}"'
    )
    run_command(ps_filter_cmd)

    # Start container
    logger.info(f"# Starting container {DOCKER_CONTAINER_NAME}...")
    result = run_command(
        f"docker start {DOCKER_CONTAINER_NAME}", capture_output=True)
    if result.returncode != 0:
        logger.error(f"Failed to start container {DOCKER_CONTAINER_NAME}")
        logger.error("Please run create_container.py first.")
        sys.exit(1)

    try:
        if is_mcp:
            logger.info("# Install MCP tools")
            # Here you can add any additional setup needed for MCP support
            # npm install -g npm && npm install && npm run build
            mcp_cmd = (
                f'docker exec -t {DOCKER_CONTAINER_NAME} /bin/sh -c "'
                f'cd {mcp_node};'
                f'/bin/sh build.sh'
                f'"'
            )
            result = subprocess.run(mcp_cmd, shell=True, check=True)
            if result.returncode != 0:
                logger.error(f"Build failed.")
                sys.exit(1)
    except subprocess.CalledProcessError as e:
        logger.error(f"Running MCP setup failed: {e}")
        sys.exit(1)

    try:
        # Run npm start inside container
        logger.info("# npm install and build inside the container...")
        build_mode = "production" if is_production else "development"
        build_cmd = f'npm install -g npm && npm install' \
            + f' && npm audit fix && ' \
            + ("npm run build:prod" if is_production else "npm run build")
        logger.info(f"# Build mode: {build_mode}")
        # npm install -g npm && npm install && npm run build
        npm_cmd = (
            f'docker exec -t {DOCKER_CONTAINER_NAME} /bin/sh -c "'
            f'cd {acting_doll_node};'
            f'{build_cmd}'
            f'"'
        )

        # Run the command and show output in real-time
        result = subprocess.run(npm_cmd, shell=True, check=True)
        if result.returncode != 0:
            logger.error(f"Build failed.")
            sys.exit(1)
        logger.info("== Build completed ==")
    except subprocess.CalledProcessError as e:
        logger.error(f"Running npm install and build failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build Cubism SDK Web project in Docker container"
    )
    parser.add_argument(
        "-p",
        "--production",
        action="store_true",
        default=False,
        help="Build in production mode (npm run build:prod)"
    )
    parser.add_argument(
        "--add_mcp",
        action="store_true",
        default=False,
        help="Support MCP server"
    )

    args = parser.parse_args()

    # Determine production mode
    is_production = args.production
    is_mcp = args.add_mcp

    work_dir = Path(__file__).parent.parent.parent.resolve()
    os.chdir(work_dir)
    config_path = Path("src").resolve().absolute() / "config.yaml"
    main(work_dir, config_path, is_production, is_mcp)
