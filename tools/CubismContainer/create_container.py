#!/usr/bin/env python3
"""
Docker container creation script for Cubism SDK Web
"""

import os
import sys
import subprocess
import yaml
import shutil
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
        # logger.info(f"  [CMD] {' '.join(cmd) if isinstance(cmd, list) else cmd}")
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


def remove_directory_and_empty_parents(work_dir, directory, max_depth=2):
    """Remove directory if it exists and is empty, recursively up to work_dir.

    Args:
        work_dir: Root directory to stop at
        directory: Target directory to remove
        max_depth: Maximum number of parent directories to check (default: 2)
    """
    if directory.exists():
        shutil.rmtree(directory)
    current = Path(directory).parent
    work_path = Path(work_dir)
    depth = 0
    while current.exists() and current != work_path and depth < max_depth:
        if not any(current.iterdir()):
            shutil.rmtree(current)
            current = current.parent
            depth += 1
        else:
            break


def main(work_dir, config_path):
    # Load settings from YAML
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse YAML configuration: {e}")
        sys.exit(1)

    DOCKER_FILE_NAME = config['docker']['dockerfile']
    DOCKER_IMAGE_NAME = config['docker']['image']['name']
    DOCKER_IMAGE_VER = config['docker']['image']['version']
    DOCKER_CONTAINER_NAME = config['docker']['container']['name']
    SERVER_PORT = config['docker']['container']['port_cubism']
    WEBSOCKET_PORT = config['docker']['container']['port_websocket']
    MCP_PORT = config['docker']['container']['port_mcp']
    GIT_FRAMEWORK_REPO = config['cubism']['git_framework_repo']
    GIT_FRAMEWORK_TAG = config['cubism']['git_framework_tag']
    GIT_FRAMEWORK_DIR_NAME = config['cubism']['git_framework_dir_name']
    GIT_SAMPLE_REPO = config['cubism']['git_sample_repo']
    GIT_SAMPLE_TAG = config['cubism']['git_sample_tag']
    GIT_SAMPLE_DIR_NAME = config['cubism']['git_sample_dir_name']
    ARCHIVE_CORE_DIR = config['cubism']['archive_core_dir']
    MODELS_DIR = config['cubism']['models_dir']
    ADAPTER_DIR = config['custom']['adapter_dir']
    FRAMEWORK_DIR = config['cubism']['framework_dir']

    INNER_SERVER_PORT = 5000
    INNER_WEBSOCKET_PORT = 8765
    INNER_MCP_PORT = 3001

    # Authentication settings
    AUTH_TOKEN = config['authentication']['token']
    REQUIRE_AUTH = str(config['authentication']['require_auth']).lower()
    ALLOWED_DIRS = ':'.join(config['authentication']['dirs'])

    dockerfile_path = Path(work_dir / DOCKER_FILE_NAME).resolve().absolute()
    adapter_dir = Path(ADAPTER_DIR).resolve().absolute()
    archive_core_path = Path(ARCHIVE_CORE_DIR).resolve().absolute()
    models_path = Path(MODELS_DIR).resolve().absolute()
    framework_dir = Path(FRAMEWORK_DIR).resolve().absolute()
    args_core_dir = "./._volume/Core"
    temp_core_dir = Path(work_dir / args_core_dir).resolve().absolute()

    # Display settings
    logger.info("=" * 50)
    logger.info("[Create Cubism SDK for Web Docker Container]")
    logger.info(f"  Git")
    logger.info(f"    Framework : {GIT_FRAMEWORK_REPO}[{GIT_FRAMEWORK_TAG}]")
    logger.info(f"    Sample    : {GIT_SAMPLE_REPO}[{GIT_SAMPLE_TAG}]")
    logger.info(f"  Files")
    logger.info(f"    Working Dir       : {work_dir}")
    logger.info(f"    Config            : {config_path}")
    logger.info(f"    Cubism Core Dir   : {archive_core_path}")
    logger.info(f"    Cubism Models Dir : {models_path}")
    logger.info(f"  Authentication")
    logger.info(f"    Auth Token        : {AUTH_TOKEN}")
    logger.info(f"    Require Auth      : {REQUIRE_AUTH}")
    logger.info(f"    Allowed Dirs      : {ALLOWED_DIRS}")
    logger.info(f"  Docker")
    logger.info(f"    dockerfile : {dockerfile_path}")
    logger.info(f"    image      : {DOCKER_IMAGE_NAME}:{DOCKER_IMAGE_VER}")
    logger.info(f"    container  : {DOCKER_CONTAINER_NAME}")
    logger.info(f"      port(HTTP)      : {SERVER_PORT}")
    logger.info(f"      port(Websocket) : {WEBSOCKET_PORT}")
    logger.info(f"      port(MCP)       : {MCP_PORT}")
    logger.info("=" * 50)

    # Check Cubism Core files
    logger.info(f"# Checking Archive Core directory: {archive_core_path}")
    if not archive_core_path.exists():
        logger.error(f"Archive core directory not found: {archive_core_path}")
        sys.exit(1)
    js_files = list(archive_core_path.glob("*core*"))
    if not js_files:
        logger.error(f"Cubism Core file not found: {archive_core_path}")
        logger.error(
            "Please download it from https://www.live2d.com/sdk/download/web/")
        sys.exit(1)

    # Remove existing containers
    logger.info("# Checking for existing containers...")
    ps_cmd = f'docker ps -a --format "{{{{.ID}}}}" --filter "ancestor={DOCKER_IMAGE_NAME}:{DOCKER_IMAGE_VER}"'
    result = run_command(ps_cmd, capture_output=True)
    if result.stdout.strip():
        container_ids = result.stdout.strip().split('\n')
        for container_id in container_ids:
            logger.info(f"  - Remove existing container: ID[{container_id}]")
            run_command(f"docker stop {container_id}", capture_output=True)
            run_command(f"docker rm {container_id}", capture_output=True)

    # Remove existing image
    logger.info("# Checking for existing images...")
    img_cmd = f"docker image ls -q {DOCKER_IMAGE_NAME}:{DOCKER_IMAGE_VER}"
    result = run_command(img_cmd, capture_output=True)
    if result.stdout.strip():
        logger.info(
            f"  - Remove existing image: {DOCKER_IMAGE_NAME}:{DOCKER_IMAGE_VER}")
        run_command(
            f"docker rmi {DOCKER_IMAGE_NAME}:{DOCKER_IMAGE_VER}", capture_output=True)

    # Build Docker image
    logger.info("# Building Docker image...")

    # Temporarily copy Core files to Dockerfile directory

    logger.info(f"# Copying Core files to {temp_core_dir}")
    try:
        remove_directory_and_empty_parents(work_dir, temp_core_dir)
        shutil.copytree(archive_core_path, temp_core_dir)
    except Exception as e:
        logger.error(f"Failed to copy Core files: {e}")
        sys.exit(1)

    try:
        build_cmd = [
            "docker", "build",
            "--build-arg", f"GIT_FRAMEWORK_REPO={GIT_FRAMEWORK_REPO}",
            "--build-arg", f"GIT_FRAMEWORK_TAG={GIT_FRAMEWORK_TAG}",
            "--build-arg", f"GIT_FRAMEWORK_DIR_NAME={GIT_FRAMEWORK_DIR_NAME}",
            "--build-arg", f"GIT_SAMPLE_REPO={GIT_SAMPLE_REPO}",
            "--build-arg", f"GIT_SAMPLE_TAG={GIT_SAMPLE_TAG}",
            "--build-arg", f"GIT_SAMPLE_DIR_NAME={GIT_SAMPLE_DIR_NAME}",
            "--build-arg", f"CORE_ARCHIVE_DIR={args_core_dir}",
            "-t", f"{DOCKER_IMAGE_NAME}:{DOCKER_IMAGE_VER}",
            "-f", str(dockerfile_path),
            "."
        ]
        result = run_command(build_cmd, shell=False, check=True)
        if result.returncode != 0:
            logger.error(f"Failed to create Docker image: {result.stderr}")
            sys.exit(1)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to build Docker image: {e}")
        sys.exit(1)
    finally:
        # Clean up temporary Core files
        logger.info("# Cleaning up temporary Core files...")
        remove_directory_and_empty_parents(work_dir, temp_core_dir)

    # Run container
    logger.info("# Creating Docker container...")
    run_cmd = [
        "docker", "container", "run",
        "--name", DOCKER_CONTAINER_NAME,
        "-dit",
        "-v", f"{adapter_dir}:/root/workspace/adapter",
        "-v", f"{models_path}:/root/workspace/Cubism/Resources",
        "-p", f"{SERVER_PORT}:{INNER_SERVER_PORT}",
        "-p", f"{WEBSOCKET_PORT}:{INNER_WEBSOCKET_PORT}",
        "-p", f"{MCP_PORT}:{INNER_MCP_PORT}",
        "-e", f"WEBSOCKET_AUTH_TOKEN={AUTH_TOKEN}",
        "-e", f"WEBSOCKET_REQUIRE_AUTH={REQUIRE_AUTH}",
        "-e", f"WEBSOCKET_ALLOWED_DIRS={ALLOWED_DIRS}",
        f"{DOCKER_IMAGE_NAME}:{DOCKER_IMAGE_VER}"
    ]
    result = run_command(run_cmd, shell=False, capture_output=True)
    if result.returncode != 0:
        logger.error(f"Failed to start Docker container: {result.stderr}")
        sys.exit(1)

    # Copy Framework files from container
    logger.info("# Copying Framework files from Docker container...")
    try:
        remove_directory_and_empty_parents(work_dir, framework_dir)
        frame_copy_cmd = [
            "docker", "cp",
            DOCKER_CONTAINER_NAME + ":/root/workspace/Cubism/" + GIT_FRAMEWORK_DIR_NAME,
            str(framework_dir)
        ]
        result = run_command(frame_copy_cmd, shell=False, check=True)
        if result.returncode != 0:
            logger.error(
                f"Failed to copy Framework files from Docker container")
    except subprocess.CalledProcessError as e:
        logger.error(
            f"Failed to copy Framework files from Docker container: {e}")

    ps_filter_cmd = (
        f'docker ps -a --filter "ancestor={DOCKER_IMAGE_NAME}:{DOCKER_IMAGE_VER}" '
        f'--format "table {{{{.ID}}}}\\t{{{{.Image}}}}\\t{{{{.Status}}}}\\t{{{{.Names}}}}\\t{{{{.Ports}}}}"'
    )
    logger.info("Docker Containers list:")
    result = run_command(ps_filter_cmd, shell=True, capture_output=False)
    if result.returncode != 0:
        logger.error("[Error] Container setup failed! --")
        sys.exit(1)
    else:
        logger.info("# -- Container setup completed successfully! --")


if __name__ == "__main__":
    work_dir = Path(__file__).parent.parent.parent.resolve()
    os.chdir(work_dir)
    config_path = Path("src").resolve().absolute() / "config.yaml"
    main(work_dir, config_path)
