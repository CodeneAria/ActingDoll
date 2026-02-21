#!/usr/bin/env python3
"""
Docker container management script for Cubism SDK Web
Unified script to manage build, clean, create, exec, start, and start_demo operations.
"""

import argparse
import os
import subprocess
import sys
import yaml
import logging
import shutil
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


# ============================================================================
# COMMAND: create
# ============================================================================
def cmd_create(work_dir, config_path):
    """Create Docker image and container."""
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
            logger.info(f"  - Removing container: {container_id}")
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
            logger.error(f"Failed to build Docker image")
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
            logger.error(f"Failed to copy Framework files")
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


# ============================================================================
# COMMAND: build
# ============================================================================
def cmd_build(work_dir, config_path, is_production=False, is_mcp=False):
    """Build project inside Docker container."""
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
        logger.error("Please run create first.")
        sys.exit(1)

    try:
        if is_mcp:
            logger.info("# Install MCP tools")
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
            + f' && npm audit fix; ' \
            + ("npm run build:prod" if is_production else "npm run build")
        logger.info(f"# Build mode: {build_mode}")
        # npm install -g npm && npm install && npm audit fix; npm run build
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


# ============================================================================
# COMMAND: clean
# ============================================================================
def cmd_clean(work_dir, config_path):
    """Clean build artifacts inside Docker container."""
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
        logger.error("Please run create first.")
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


# ============================================================================
# COMMAND: exec
# ============================================================================
def cmd_exec(work_dir, config_path):
    """Execute shell inside Docker container."""
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

    # Show running containers
    logger.info("=" * 50)
    logger.info("[Docker Containers Running]")
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
        logger.error("Please run create first.")
        sys.exit(1)

    # Run npm start inside container
    logger.info("# Executing shell inside the container...")
    npm_cmd = (
        f'docker exec -it {DOCKER_CONTAINER_NAME} /bin/sh'
    )

    try:
        # Run the command and show output in real-time
        subprocess.run(npm_cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        # logger.error(f"[Error] executing shell: {e}")
        pass
    except KeyboardInterrupt:
        logger.info("# Shutting down...")
        sys.exit(0)


# ============================================================================
# COMMAND: start
# ============================================================================
def cmd_start(work_dir, config_path):
    """Start application server."""
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

    INNER_SERVER_PORT = 5000
    INNER_WEBSOCKET_PORT = 8765
    INNER_MCP_PORT = 3001

    DOCKER_IMAGE_NAME = config['docker']['image']['name']
    DOCKER_IMAGE_VER = config['docker']['image']['version']
    DOCKER_CONTAINER_NAME = config['docker']['container']['name']

    # Authentication settings
    AUTH_TOKEN = config['authentication']['token']
    REQUIRE_AUTH = str(config['authentication']['require_auth']).lower()
    ALLOWED_DIRS = ':'.join(config['authentication']['dirs'])

    server_dir = f"/root/workspace/adapter"

    # Show running containers
    logger.info("=" * 50)
    logger.info("[Start Cubism SDK for Web]")
    ps_filter_cmd = (
        f'docker ps -a --filter "ancestor={DOCKER_IMAGE_NAME}:{DOCKER_IMAGE_VER}" '
        f'--format "table {{{{.ID}}}}\\t{{{{.Image}}}}\\t{{{{.Status}}}}\\t{{{{.Names}}}}\\t{{{{.Ports}}}}"'
    )
    run_command(ps_filter_cmd)
    logger.info("=" * 50)

    # Restart container
    logger.info(f"# Restarting container {DOCKER_CONTAINER_NAME}...")
    result = run_command(
        f"docker restart {DOCKER_CONTAINER_NAME}", capture_output=True)
    if result.returncode != 0:
        logger.error(f"Failed to start container {DOCKER_CONTAINER_NAME}")
        logger.error("Please run create first.")
        sys.exit(1)

    # Run npm start inside container
    logger.info("# Running npm start...")
    npm_cmd = (
        f'docker exec -t '
        f'-e WEBSOCKET_AUTH_TOKEN={AUTH_TOKEN} '
        f'-e WEBSOCKET_REQUIRE_AUTH={REQUIRE_AUTH} '
        f'-e WEBSOCKET_ALLOWED_DIRS={ALLOWED_DIRS} '
        f'{DOCKER_CONTAINER_NAME} /bin/sh -c "'
        f"export PORT_WEBSOCKET_NUMBER={INNER_WEBSOCKET_PORT};"
        f"export PORT_HTTP_NUMBER={INNER_SERVER_PORT};"
        f"export PORT_MCP_NUMBER={INNER_MCP_PORT};"
        f'cd {server_dir} && /bin/sh start.sh"'
    )

    try:
        # Run the command and show output in real-time
        subprocess.run(npm_cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to run npm start: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("# Shutting down...")
        run_command(
            f"docker stop {DOCKER_CONTAINER_NAME}", capture_output=True)
        sys.exit(0)


# ============================================================================
# COMMAND: start_demo
# ============================================================================
def cmd_start_demo(work_dir, config_path):
    """Start demo application."""
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
    GIT_SAMPLE_DIR_NAME = config['cubism']['git_sample_dir_name']

    node_dir = f"/root/workspace/Cubism/{GIT_SAMPLE_DIR_NAME}/Samples/TypeScript/Demo"

    # Show running containers
    logger.info("=" * 50)
    logger.info("[Start Cubism SDK for Web]")
    ps_filter_cmd = (
        f'docker ps -a --filter "ancestor={DOCKER_IMAGE_NAME}:{DOCKER_IMAGE_VER}" '
        f'--format "table {{{{.ID}}}}\\t{{{{.Image}}}}\\t{{{{.Status}}}}\\t{{{{.Names}}}}\\t{{{{.Ports}}}}"'
    )
    run_command(ps_filter_cmd)
    logger.info("=" * 50)

    # Start container
    logger.info(f"# Restarting container {DOCKER_CONTAINER_NAME}...")
    result = run_command(
        f"docker restart {DOCKER_CONTAINER_NAME}", capture_output=True)
    if result.returncode != 0:
        logger.error(f"Failed to start container {DOCKER_CONTAINER_NAME}")
        logger.error("Please run create first.")
        sys.exit(1)

    # Run npm start inside container
    logger.info("# Running npm start inside the container...")
    npm_cmd = (
        f'docker exec -t {DOCKER_CONTAINER_NAME} /bin/sh '
        f'-c "cd {node_dir} && npm run start"'
    )

    try:
        # Run the command and show output in real-time
        subprocess.run(npm_cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"[Error] running npm start: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("# Shutting down...")
        run_command(
            f"docker stop {DOCKER_CONTAINER_NAME}", capture_output=True)
        sys.exit(0)


# ============================================================================
# MAIN
# ============================================================================
def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Unified Docker container management for Cubism SDK Web"
    )
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # create command
    subparsers.add_parser(
        'create',
        help='Create Docker image and container'
    )

    # build command
    build_parser = subparsers.add_parser(
        'build',
        help='Build project inside Docker container'
    )
    build_parser.add_argument(
        '-p', '--production',
        action='store_true',
        default=False,
        help='Build in production mode (npm run build:prod)'
    )
    build_parser.add_argument(
        '--add_mcp',
        action='store_true',
        default=False,
        help='Support MCP server'
    )

    # clean command
    subparsers.add_parser(
        'clean',
        help='Clean build artifacts inside Docker container'
    )

    # exec command
    subparsers.add_parser(
        'exec',
        help='Execute shell inside Docker container'
    )

    # start command
    subparsers.add_parser(
        'start',
        help='Start application server'
    )

    # start_demo command
    subparsers.add_parser(
        'start_demo',
        help='Start demo application'
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    work_dir = Path(__file__).parent.parent.parent.resolve()
    os.chdir(work_dir)
    config_path = Path("src").resolve().absolute() / "config.yaml"

    # Execute command
    if args.command == 'create':
        cmd_create(work_dir, config_path)
    elif args.command == 'build':
        cmd_build(work_dir, config_path, args.production, args.add_mcp)
    elif args.command == 'clean':
        cmd_clean(work_dir, config_path)
    elif args.command == 'exec':
        cmd_exec(work_dir, config_path)
    elif args.command == 'start':
        cmd_start(work_dir, config_path)
    elif args.command == 'start_demo':
        cmd_start_demo(work_dir, config_path)


if __name__ == "__main__":
    main()
