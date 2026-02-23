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
try:
    from importlib.metadata import version as get_version
    __version__ = get_version('acting-doll')
except Exception:
    __version__ = 'latest'


class ConfigActingDoll:
    """Configuration class for Acting Doll project."""

    def __init__(self, work_dir: Path):
        self.work_dir = work_dir
        self.DOCKER_FILE_NAME = self._path("Dockerfile")
        self.DOCKER_IMAGE_NAME = "image_acting_doll"
        self.DOCKER_IMAGE_VER = __version__
        self.DOCKER_CONTAINER_NAME = "server_acting_doll"

        self.CUBISM_DIR = "/root/workspace/Cubism"
        self.CUBISM_Resources_DIR = f"{self.CUBISM_DIR}/Resources"
        self.INNER_SERVER_PORT = 8080
        self.INNER_WEBSOCKET_PORT = 8765
        self.INNER_MCP_PORT = 3001

        # Authentication settings
        self.AUTH_TOKEN: bool = True
        self.REQUIRE_AUTH: str = "your_authentication_token_here"
        self.ALLOWED_DIRS = []

        self.server_dir = f"/root/workspace/adapter"

        self.acting_doll_dir = self.server_dir + f"/acting_doll"
        self.acting_doll_server_dir = self.server_dir + f"/server"

        self.SERVER_PORT: int = 8080
        self.WEBSOCKET_PORT: int = 8765
        self.MCP_PORT: int = 3001

        self.GIT_FRAMEWORK_REPO = "https://github.com/Live2D/CubismWebFramework.git"
        self.GIT_FRAMEWORK_TAG = "5-r.5-beta.3"
        self.GIT_FRAMEWORK_DIR_NAME = "Framework"
        self.GIT_SAMPLE_REPO = "https://github.com/Live2D/CubismWebSamples.git"
        self.GIT_SAMPLE_TAG = "5-r.5-beta.3"
        self.GIT_SAMPLE_DIR_NAME = "Samples"

        # Authentication settings

        self.adapter_dir = Path(self.work_dir / "src/adapter").resolve().absolute()
        self.archive_core_path = Path(self.work_dir / "src/Cubism/Core").resolve().absolute()
        self.models_path = Path(self.work_dir / "src/Cubism/Resources").resolve().absolute()
        self.framework_dir = Path(self.work_dir / "src/Cubism/Framework").resolve().absolute()
        self.args_core_dir = "./._volume/Core"
        self.temp_core_dir = Path(self.work_dir / self.args_core_dir).resolve().absolute()

        self.config_path = Path(self.work_dir / "src/config.yaml").resolve().absolute()

    def _path(self, path_str) -> Path:
        if path_str is None:
            return path_str
        path = Path(path_str)
        if path.exists():
            return path.resolve().absolute()
        path = Path(self.work_dir / path_str)
        if path.exists():
            return path.resolve().absolute()
        return path.resolve().absolute()

    def load_from_yaml(self, config_path):
        """Load configuration from YAML file."""
        try:
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                if config is None:
                    return
                # Load Docker settings
                if 'docker' in config:
                    docker = config['docker']
                    self.DOCKER_FILE_NAME = self._path(docker.get('dockerfile', self.DOCKER_FILE_NAME))
                    if 'image' in docker:
                        self.DOCKER_IMAGE_NAME = docker['image'].get('name', self.DOCKER_IMAGE_NAME)
                        self.DOCKER_IMAGE_VER = docker['image'].get('version', self.DOCKER_IMAGE_VER)
                    if 'container' in docker:
                        self.DOCKER_CONTAINER_NAME = docker['container'].get('name', self.DOCKER_CONTAINER_NAME)
                        self.SERVER_PORT = docker['container'].get('port_cubism', self.SERVER_PORT)
                        self.WEBSOCKET_PORT = docker['container'].get('port_websocket', self.WEBSOCKET_PORT)
                        self.MCP_PORT = docker['container'].get('port_mcp', self.MCP_PORT)

                # Load Cubism settings
                if 'cubism' in config:
                    cubism = config['cubism']
                    self.GIT_SAMPLE_DIR_NAME = cubism.get('git_sample_dir_name', self.GIT_SAMPLE_DIR_NAME)
                    self.GIT_FRAMEWORK_REPO = cubism.get('git_framework_repo', self.GIT_FRAMEWORK_REPO)
                    self.GIT_FRAMEWORK_TAG = cubism.get('git_framework_tag', self.GIT_FRAMEWORK_TAG)
                    self.GIT_FRAMEWORK_DIR_NAME = cubism.get('git_framework_dir_name', self.GIT_FRAMEWORK_DIR_NAME)
                    self.GIT_SAMPLE_REPO = cubism.get('git_sample_repo', self.GIT_SAMPLE_REPO)
                    self.GIT_SAMPLE_TAG = cubism.get('git_sample_tag', self.GIT_SAMPLE_TAG)
                    self.archive_core_path = self._path(cubism.get('archive_core_dir', self.archive_core_path))
                    self.models_path = self._path(cubism.get('models_dir', self.models_path))
                    self.framework_dir = self._path(cubism.get('framework_dir', self.framework_dir))
                if 'authentication' in config:
                    authentication = config['authentication']
                    self.AUTH_TOKEN = authentication.get('token', self.AUTH_TOKEN)
                    self.REQUIRE_AUTH = str(authentication.get('require_auth', self.REQUIRE_AUTH)).lower()
                    self.ALLOWED_DIRS = ':'.join(authentication.get('dirs', self.ALLOWED_DIRS))

                # Load Custom settings
                if 'custom' in config:
                    custom = config['custom']
                    self.adapter_dir = self._path(custom.get('adapter_dir', self.adapter_dir))
                self.config_path = self._path(config_path)
        ##
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML configuration: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            sys.exit(1)

    def apply_args(self, args):
        """Apply command-line arguments to override config."""
        if hasattr(args, 'DOCKER_IMAGE_NAME') and args.DOCKER_IMAGE_NAME:
            self.DOCKER_IMAGE_NAME = args.DOCKER_IMAGE_NAME
        if hasattr(args, 'DOCKER_IMAGE_VERsion') and args.DOCKER_IMAGE_VERsion:
            self.DOCKER_IMAGE_VER = args.DOCKER_IMAGE_VERsion
        if hasattr(args, 'DOCKER_CONTAINER_NAME') and args.DOCKER_CONTAINER_NAME:
            self.DOCKER_CONTAINER_NAME = args.DOCKER_CONTAINER_NAME
        if hasattr(args, 'port_http') and args.port_http:
            self.SERVER_PORT = args.port_http
        # if hasattr(args, 'port_websocket') and args.WEBSOCKET_PORT:
        #    self.WEBSOCKET_PORT = args.WEBSOCKET_PORT
        # if hasattr(args, 'port_mcp') and args.MCP_PORT:
        #    self.MCP_PORT = args.MCP_PORT
        # if hasattr(args, 'auth_token') and args.auth_token:
        #    self.AUTH_TOKEN = args.auth_token
        #    self.REQUIRE_AUTH = True


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


# ============================================================================
# COMMAND: create
# ============================================================================
def cmd_create(config: ConfigActingDoll):
    """Create Docker image and container."""

    # Display settings
    logger.info("=" * 50)
    logger.info("[Create Cubism SDK for Web Docker Container]")
    logger.info(f"  Git")
    logger.info(f"    Framework : {config.GIT_FRAMEWORK_REPO}[{config.GIT_FRAMEWORK_TAG}]")
    logger.info(f"    Sample    : {config.GIT_SAMPLE_REPO}[{config.GIT_SAMPLE_TAG}]")
    logger.info(f"  Files")
    logger.info(f"    Working Dir       : {config.work_dir}")
    logger.info(f"    Config            : {config.config_path}")
    logger.info(f"    Cubism Core Dir   : {config.archive_core_path}")
    logger.info(f"    Cubism Models Dir : {config.models_path}")
    logger.info(f"  Authentication")
    logger.info(f"    Auth Token        : {config.AUTH_TOKEN}")
    logger.info(f"    Require Auth      : {config.REQUIRE_AUTH}")
    logger.info(f"    Allowed Dirs      : {config.ALLOWED_DIRS}")
    logger.info(f"  Docker")
    logger.info(f"    dockerfile : {config.DOCKER_FILE_NAME}")
    logger.info(f"    image      : {config.DOCKER_IMAGE_NAME}:{config.DOCKER_IMAGE_VER}")
    logger.info(f"    container  : {config.DOCKER_CONTAINER_NAME}")
    logger.info(f"      port(HTTP)      : {config.SERVER_PORT}")
    logger.info(f"      port(Websocket) : {config.WEBSOCKET_PORT}")
    logger.info(f"      port(MCP)       : {config.MCP_PORT}")
    logger.info("=" * 50)

    # Check Cubism Core files
    logger.info(f"# Checking Archive Core directory: {config.archive_core_path}")
    if not config.archive_core_path.exists():
        logger.error(f"Archive core directory not found: {config.archive_core_path}")
        sys.exit(1)
    js_files = list(config.archive_core_path.glob("*core*"))
    if not js_files:
        logger.error(f"Cubism Core file not found: {config.archive_core_path}")
        logger.error(
            "Please download it from https://www.live2d.com/sdk/download/web/")
        sys.exit(1)

    # Remove existing containers
    logger.info("# Checking for existing containers...")
    ps_cmd = f'docker ps -a --format "{{{{.ID}}}}" --filter "ancestor={config.DOCKER_IMAGE_NAME}:{config.DOCKER_IMAGE_VER}"'
    result = run_command(ps_cmd, capture_output=True)
    if result.stdout.strip():
        container_ids = result.stdout.strip().split('\n')
        for container_id in container_ids:
            logger.info(f"  - Removing container: {container_id}")
            run_command(f"docker stop {container_id}", capture_output=True)
            run_command(f"docker rm {container_id}", capture_output=True)

    # Remove existing image
    logger.info("# Checking for existing images...")
    img_cmd = f"docker image ls -q {config.DOCKER_IMAGE_NAME}:{config.DOCKER_IMAGE_VER}"
    result = run_command(img_cmd, capture_output=True)
    if result.stdout.strip():
        logger.info(
            f"  - Remove existing image: {config.DOCKER_IMAGE_NAME}:{config.DOCKER_IMAGE_VER}")
        run_command(
            f"docker rmi {config.DOCKER_IMAGE_NAME}:{config.DOCKER_IMAGE_VER}", capture_output=True)

    # Build Docker image
    logger.info("# Building Docker image...")

    # Temporarily copy Core files to Dockerfile directory
    logger.info(f"# Copying Core files to {config.temp_core_dir}...")
    try:
        remove_directory_and_empty_parents(config.work_dir, config.temp_core_dir)
        shutil.copytree(config.archive_core_path, config.temp_core_dir)
    except Exception as e:
        logger.error(f"Failed to copy Core files: {e}")
        sys.exit(1)

    try:
        build_cmd = [
            "docker", "build",
            "--build-arg", f"GIT_FRAMEWORK_REPO={config.GIT_FRAMEWORK_REPO}",
            "--build-arg", f"GIT_FRAMEWORK_TAG={config.GIT_FRAMEWORK_TAG}",
            "--build-arg", f"GIT_FRAMEWORK_DIR_NAME={config.GIT_FRAMEWORK_DIR_NAME}",
            "--build-arg", f"GIT_SAMPLE_REPO={config.GIT_SAMPLE_REPO}",
            "--build-arg", f"GIT_SAMPLE_TAG={config.GIT_SAMPLE_TAG}",
            "--build-arg", f"GIT_SAMPLE_DIR_NAME={config.GIT_SAMPLE_DIR_NAME}",
            "--build-arg", f"CORE_ARCHIVE_DIR={config.args_core_dir}",
            "-t", f"{config.DOCKER_IMAGE_NAME}:{config.DOCKER_IMAGE_VER}",
            "-f", str(config.DOCKER_FILE_NAME),
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
        remove_directory_and_empty_parents(config.work_dir, config.temp_core_dir)

    # Run container
    logger.info("# Creating Docker container...")
    run_cmd = [
        "docker", "container", "run",
        "--name", config.DOCKER_CONTAINER_NAME,
        "-dit",
        "-v", f"{config.adapter_dir}:{config.server_dir}",
        "-v", f"{config.models_path}:{config.CUBISM_Resources_DIR}",
        "-p", f"{config.SERVER_PORT}:{config.INNER_SERVER_PORT}",
        "-p", f"{config.WEBSOCKET_PORT}:{config.INNER_WEBSOCKET_PORT}",
        "-p", f"{config.MCP_PORT}:{config.INNER_MCP_PORT}",
        "-e", f"WEBSOCKET_AUTH_TOKEN={config.AUTH_TOKEN}",
        "-e", f"WEBSOCKET_REQUIRE_AUTH={config.REQUIRE_AUTH}",
        "-e", f"WEBSOCKET_ALLOWED_DIRS={':'.join(config.ALLOWED_DIRS)}",
        f"{config.DOCKER_IMAGE_NAME}:{config.DOCKER_IMAGE_VER}"
    ]
    result = run_command(run_cmd, shell=False, capture_output=True)
    if result.returncode != 0:
        logger.error(f"Failed to start Docker container: {result.stderr}")
        sys.exit(1)

    # Copy Framework files from container
    logger.info("# Copying Framework files from Docker container...")
    try:
        remove_directory_and_empty_parents(config.work_dir, config.framework_dir)
        frame_copy_cmd = [
            "docker", "cp",
            config.DOCKER_CONTAINER_NAME + f":{config.CUBISM_DIR}/" + config.GIT_FRAMEWORK_DIR_NAME,
            str(config.framework_dir)
        ]
        result = run_command(frame_copy_cmd, shell=False, check=True)
        if result.returncode != 0:
            logger.error(f"Failed to copy Framework files")
    except subprocess.CalledProcessError as e:
        logger.error(
            f"Failed to copy Framework files from Docker container: {e}")

    ps_filter_cmd = (
        f'docker ps -a --filter "ancestor={config.DOCKER_IMAGE_NAME}:{config.DOCKER_IMAGE_VER}" '
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
def cmd_build(config: ConfigActingDoll, is_production=False, is_mcp=False):
    """Build project inside Docker container."""

    # Show running containers
    logger.info("[Build model inside Cubism SDK for Web container]")
    ps_filter_cmd = (
        f'docker ps -a --filter "ancestor={config.DOCKER_IMAGE_NAME}:{config.DOCKER_IMAGE_VER}" '
        f'--format "table {{{{.ID}}}}\\t{{{{.Image}}}}\\t{{{{.Status}}}}\\t{{{{.Names}}}}\\t{{{{.Ports}}}}"'
    )
    run_command(ps_filter_cmd)

    # Start container
    logger.info(f"# Starting container {config.DOCKER_CONTAINER_NAME}...")
    result = run_command(
        f"docker start {config.DOCKER_CONTAINER_NAME}", capture_output=True)
    if result.returncode != 0:
        logger.error(f"Failed to start container {config.DOCKER_CONTAINER_NAME}")
        logger.error("Please run create first.")
        sys.exit(1)

    try:
        if is_mcp:
            logger.info("# Install MCP tools")
            mcp_cmd = (
                f'docker exec -t {config.DOCKER_CONTAINER_NAME} /bin/sh -c "'
                f'cd {config.acting_doll_server_dir};'
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
            f'docker exec -t {config.DOCKER_CONTAINER_NAME} /bin/sh -c "'
            f'cd {config.acting_doll_dir};'
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
def cmd_clean(config: ConfigActingDoll):
    """Clean build artifacts inside Docker container."""

    # Show running containers
    logger.info("=" * 50)
    logger.info("[Clean build artifacts inside Cubism SDK for Web container]")
    ps_filter_cmd = (
        f'docker ps -a --filter "ancestor={config.DOCKER_IMAGE_NAME}:{config.DOCKER_IMAGE_VER}" '
        f'--format "table {{{{.ID}}}}\\t{{{{.Image}}}}\\t{{{{.Status}}}}\\t{{{{.Names}}}}\\t{{{{.Ports}}}}"'
    )
    run_command(ps_filter_cmd)
    logger.info("=" * 50)

    # Start container
    logger.info(f"# Starting container {config.DOCKER_CONTAINER_NAME}...")
    result = run_command(
        f"docker start {config.DOCKER_CONTAINER_NAME}", capture_output=True)
    if result.returncode != 0:
        logger.error(f"Failed to start container {config.DOCKER_CONTAINER_NAME}")
        logger.error("Please run create first.")
        sys.exit(1)

    # Run npm start inside container
    logger.info("# npm run clean inside the container...")
    # npm install -g npm && npm install && npm run build
    npm_cmd = (
        f'docker exec -t {config.DOCKER_CONTAINER_NAME} /bin/sh -c "'
        f'cd {config.acting_doll_dir}'
        f' && npm run clean'
        f' && rm -rf public'
        f' && rm -rf node_modules;'
        f'cd {config.acting_doll_server_dir}'
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
def cmd_exec(config: ConfigActingDoll):
    """Execute shell inside Docker container."""

    # Show running containers
    logger.info("=" * 50)
    logger.info("[Docker Containers Running]")
    ps_filter_cmd = (
        f'docker ps -a --filter "ancestor={config.DOCKER_IMAGE_NAME}:{config.DOCKER_IMAGE_VER}" '
        f'--format "table {{{{.ID}}}}\\t{{{{.Image}}}}\\t{{{{.Status}}}}\\t{{{{.Names}}}}\\t{{{{.Ports}}}}"'
    )
    run_command(ps_filter_cmd)
    logger.info("=" * 50)

    # Start container
    logger.info(f"# Starting container {config.DOCKER_CONTAINER_NAME}...")
    result = run_command(
        f"docker start {config.DOCKER_CONTAINER_NAME}", capture_output=True)
    if result.returncode != 0:
        logger.error(f"Failed to start container {config.DOCKER_CONTAINER_NAME}")
        logger.error("Please run create first.")
        sys.exit(1)

    # Run npm start inside container
    logger.info("# Executing shell inside the container...")
    npm_cmd = (
        f'docker exec -it {config.DOCKER_CONTAINER_NAME} /bin/sh'
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
def cmd_start(config: ConfigActingDoll):
    """Start application server."""

    # Show running containers
    logger.info("=" * 50)
    logger.info("[Start Cubism SDK for Web]")
    ps_filter_cmd = (
        f'docker ps -a --filter "ancestor={config.DOCKER_IMAGE_NAME}:{config.DOCKER_IMAGE_VER}" '
        f'--format "table {{{{.ID}}}}\\t{{{{.Image}}}}\\t{{{{.Status}}}}\\t{{{{.Names}}}}\\t{{{{.Ports}}}}"'
    )
    run_command(ps_filter_cmd)
    logger.info("=" * 50)

    # Restart container
    logger.info(f"# Restarting container {config.DOCKER_CONTAINER_NAME}...")
    result = run_command(
        f"docker restart {config.DOCKER_CONTAINER_NAME}", capture_output=True)
    if result.returncode != 0:
        logger.error(f"Failed to start container {config.DOCKER_CONTAINER_NAME}")
        logger.error("Please run create first.")
        sys.exit(1)

    # Run npm start inside container
    logger.info("# Running npm start...")
    npm_cmd = (
        f'docker exec -t '
        f'-e WEBSOCKET_AUTH_TOKEN={config.AUTH_TOKEN} '
        f'-e WEBSOCKET_REQUIRE_AUTH={config.REQUIRE_AUTH} '
        f'-e WEBSOCKET_ALLOWED_DIRS={config.ALLOWED_DIRS} '
        f'{config.DOCKER_CONTAINER_NAME} /bin/sh -c "'
        f"export PORT_WEBSOCKET_NUMBER={config.INNER_WEBSOCKET_PORT};"
        f"export PORT_HTTP_NUMBER={config.INNER_SERVER_PORT};"
        f"export PORT_MCP_NUMBER={config.INNER_MCP_PORT};"
        f'cd {config.server_dir} && /bin/sh start.sh"'
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
            f"docker stop {config.DOCKER_CONTAINER_NAME}", capture_output=True)
        sys.exit(0)


# ============================================================================
# COMMAND: start_demo
# ============================================================================
def cmd_start_demo(config: ConfigActingDoll):
    """Start demo application."""

    demo_dir = f"{config.CUBISM_DIR}/{config.GIT_SAMPLE_DIR_NAME}/Samples/TypeScript/Demo"

    # Show running containers
    logger.info("=" * 50)
    logger.info("[Start Cubism SDK for Web]")
    ps_filter_cmd = (
        f'docker ps -a --filter "ancestor={config.DOCKER_IMAGE_NAME}:{config.DOCKER_IMAGE_VER}" '
        f'--format "table {{{{.ID}}}}\\t{{{{.Image}}}}\\t{{{{.Status}}}}\\t{{{{.Names}}}}\\t{{{{.Ports}}}}"'
    )
    run_command(ps_filter_cmd)
    logger.info("=" * 50)

    # Start container
    logger.info(f"# Restarting container {config.DOCKER_CONTAINER_NAME}...")
    result = run_command(
        f"docker restart {config.DOCKER_CONTAINER_NAME}", capture_output=True)
    if result.returncode != 0:
        logger.error(f"Failed to start container {config.DOCKER_CONTAINER_NAME}")
        logger.error("Please run create first.")
        sys.exit(1)

    # Run npm start inside container
    logger.info("# Running npm start inside the container...")
    npm_cmd = (
        f'docker exec -t {config.DOCKER_CONTAINER_NAME} /bin/sh '
        f'-c "cd {demo_dir} && npm run start -- --port {config.INNER_SERVER_PORT}"'
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
            f"docker stop {config.DOCKER_CONTAINER_NAME}", capture_output=True)
        sys.exit(0)


# ============================================================================
# MAIN
# ============================================================================
def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Unified Docker container management for Cubism SDK Web"
    )

    # Global arguments
    parser.add_argument(
        '-c', '--config',
        type=str,
        default=None,
        help='Path to config.yaml (default: config.yaml)'
    )
    parser.add_argument(
        '-w', '--workspace',
        type=str,
        default=None,
        help='Path to workspace folder (default: current folder)'
    )

    # Docker image settings
    parser.add_argument(
        '--docker-image-name',
        type=str,
        default='image_acting_doll',
        help='Docker image name (overrides config.yaml)'
    )
    parser.add_argument(
        '--docker-image-version',
        type=str,
        default=None,
        help='Docker image version (overrides config.yaml)'
    )

    # Docker container settings
    parser.add_argument(
        '--docker-container-name',
        type=str,
        default='server_acting_doll',
        help='Docker container name (overrides config.yaml)'
    )

    # Port mappings
    parser.add_argument(
        '--port-http',
        type=int,
        default=8080,
        help='HTTP port mapping (overrides config.yaml)'
    )
    parser.add_argument(
        '--port-websocket',
        type=int,
        default=8765,
        help='WebSocket port mapping (overrides config.yaml)'
    )
    parser.add_argument(
        '--port-mcp',
        type=int,
        default=3001,
        help='MCP port mapping (overrides config.yaml)'
    )

    # Authentication settings
    parser.add_argument(
        '--auth-token',
        type=str,
        default=None,
        help='Authentication token (overrides config.yaml)'
    )

    # Directory settings
    parser.add_argument(
        '--dirs-models',
        type=str,
        default=None,
        help='Directories for models (overrides config.yaml)'
    )
    parser.add_argument(
        '--cubism-core-zip',
        type=str,
        default=None,
        help='Path to Cubism Core ZIP file (overrides config.yaml)'
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

    if args.workspace:
        work_dir = Path(args.workspace).resolve().absolute()
    else:
        work_dir = Path(__file__).parent.parent.parent.resolve()
    os.chdir(work_dir)

    # Create and load configuration
    config = ConfigActingDoll(work_dir)

    # Load from YAML
    if args.config:
        config_path = Path(args.config).resolve().absolute()
        config.load_from_yaml(config_path)
    # Apply command-line arguments
    config.apply_args(args)

    # Execute command
    if args.command == 'create':
        cmd_create(config)
    elif args.command == 'build':
        cmd_build(config, args.production, args.add_mcp)
    elif args.command == 'clean':
        cmd_clean(config)
    elif args.command == 'exec':
        cmd_exec(config)
    elif args.command == 'start':
        cmd_start(config)
    elif args.command == 'start_demo':
        cmd_start_demo(config)


if __name__ == "__main__":
    main()
