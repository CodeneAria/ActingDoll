#!/usr/bin/env python3
"""
Docker container run script for Cubism SDK Web
"""

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


def main(work_dir, config_path):
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

    node_dir = f"/root/workspace/adapter/acting_doll"
    pip_node = f"/root/workspace/adapter/server"

    # Show running containers
    logger.info("=" * 50)
    logger.info("[Clean build artifacts inside Cubism SDK for Web container]")
    ps_filter_cmd = (
        f'docker ps -a --filter "ancestor={DOCKER_IMAGE_NAME}:{DOCKER_IMAGE_VER}" '
        f'--format "table {{{{.ID}}}}\\t{{{{.Image}}}}\\t{{{{.Status}}}}\\t{{{{.Names}}}}\\t{{{{.Ports}}}}"'
    )
    run_command(ps_filter_cmd)
    logger.info("=" * 50)

    # Start container
    logger.info(f"# Starting container {DOCKER_CONTAINER_NAME}...")
    result = run_command(
        f"docker start {DOCKER_CONTAINER_NAME}", capture_output=True)
    if result.returncode != 0:
        logger.error(f"Failed to start container {DOCKER_CONTAINER_NAME}")
        logger.error("Please run create_container.py first.")
        sys.exit(1)

    # Run npm start inside container
    logger.info("# npm run clean inside the container...")
    # npm install -g npm && npm install && npm run build
    npm_cmd = (
        f'docker exec -t {DOCKER_CONTAINER_NAME} /bin/sh -c "'
        f'cd {node_dir}'
        f' && npm run clean'
        f' && rm -rf public'
        f' && rm -rf node_modules;'
        f'cd {pip_node}'
        f' && pip uninstall acting-doll-server'
        f' && rm -rf dist/;'
        f'"'
    )

    try:
        # Run the command and show output in real-time
        subprocess.run(npm_cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Running npm run clean failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("# Shutting down...")
        sys.exit(0)


if __name__ == "__main__":
    work_dir = Path(__file__).parent.parent.parent.resolve()
    os.chdir(work_dir)
    config_path = Path("src").resolve().absolute() / "config.yaml"
    main(work_dir, config_path)
