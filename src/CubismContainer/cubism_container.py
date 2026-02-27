#!/usr/bin/env python3
"""
Docker container management script for Cubism SDK Web
Unified script to manage build, clean, create, exec, start, and start_demo operations.
"""

import argparse
import os
import subprocess
import sys
import time
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


# ============================================================================
# Configuration Class
# ============================================================================
class ConfigActingDoll:
    """Configuration class for Acting Doll project."""

    def yaml_str(self) -> str:
        yaml_str = yaml.dump({
            "docker_container_name": str(self.DOCKER_CONTAINER_NAME),
            "create": {
                "workspace": str(self.WORKSPACE),
                "moc3_file": str(self.MOC3_FILE.relative_to(self.WORKSPACE).as_posix()),
                "sdk_archive": str(self.SDK_ARCHIVE.relative_to(self.WORKSPACE).as_posix()),
                "dockerfile": str(self.DOCKER_FILE_NAME.relative_to(self.WORKSPACE).as_posix()),
                "code_dir": str(self.CODE_DIRECTORY.relative_to(self.WORKSPACE).as_posix()),
                "docker_image_name": self.DOCKER_IMAGE_NAME
            },
            "settings": {
                "port": {
                    "http": self.PORT_CUBISM,
                    "websocket": self.PORT_WEBSOCKET,
                    "mcp": self.PORT_MCP
                },
                "authentication": {
                    "token": str(self.AUTH_TOKEN)
                },
                "output_yaml": self.OUTPUT_YAML
            }
        }, sort_keys=False)
        return yaml_str

    def __init__(self, work_dir: Path):
        self.WORKSPACE = Path(work_dir).resolve().absolute() if work_dir else Path(__file__).parent.parent.resolve()
        # Default configuration values: Create command
        self.DOCKER_FILE_NAME = self._path('src/CubismContainer/volume/Dockerfile')
        self.SDK_ARCHIVE = self._path('archives/CubismSdkForWeb-5-r.5-beta.3.zip')
        self.MOC3_FILE = self._path('src/adapter/Cubism/Resources/Haru/Haru.moc3')
        self.CODE_DIRECTORY = self._path('src/adapter')
        self.DOCKER_IMAGE_NAME = 'acting_doll_image'
        self.DOCKER_IMAGE_VER = 'latest'
        self.DOCKER_CONTAINER_NAME = 'acting_doll_server_sample'

        # Build settings
        self.PRODUCTION: bool = True
        self.OUTPUT_YAML: bool = True

        # Authentication settings
        self.PORT_CUBISM: int = 8080
        self.PORT_WEBSOCKET: int = 8765
        self.PORT_MCP: int = 3001
        self.REQUIRE_AUTH: bool = False
        self.AUTH_TOKEN: str = ""
        self.ALLOWED_DIRS = [
            "/root/workspace/adapter/allowed"
        ]

        # Default configuration values: Cubism SDK Web
        self.VOLUME_SHARE = True
        self.root_dir = "/root/workspace/adapter"

        self.GIT_FRAMEWORK_REPO = "https://github.com/Live2D/CubismWebFramework.git"
        self.GIT_FRAMEWORK_TAG = "5-r.5-beta.3"
        self.GIT_FRAMEWORK_DIR_NAME = "Framework"
        self.GIT_SAMPLE_REPO = "https://github.com/Live2D/CubismWebSamples.git"
        self.GIT_SAMPLE_TAG = "5-r.5-beta.3"
        self.GIT_SAMPLE_DIR_NAME = "Samples"

    def _path(self, path_str) -> Path:
        try:
            path = Path(path_str)
            if path.exists():
                return path.resolve().absolute()

            path = Path(self.WORKSPACE / path_str)
            if path.exists():
                return path.resolve().absolute()
        except:
            return None
        return None

    def load_from_yaml(self, config_str: str):
        """Load configuration from YAML file."""
        try:
            if config_str is None:
                return
            config_path = self._path(config_str)
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                if config is None:
                    return

                # Load Docker settings
                if 'docker_container_name' in config:
                    self.DOCKER_CONTAINER_NAME = config.get('docker_container_name', self.DOCKER_CONTAINER_NAME)
                if 'create' in config:
                    create = config['create']
                    self.WORKSPACE = Path(create.get('workspace', self.WORKSPACE)).resolve().absolute()
                    self.DOCKER_FILE_NAME = self._path(create.get('dockerfile', self.DOCKER_FILE_NAME))
                    self.SDK_ARCHIVE = self._path(create.get('sdk_archive', self.SDK_ARCHIVE))
                    self.MOC3_FILE = self._path(create.get('moc3_file', self.MOC3_FILE))
                    self.CODE_DIRECTORY = self._path(create.get('code_dir', self.CODE_DIRECTORY))
                    self.DOCKER_IMAGE_NAME = create.get('docker_image_name', self.DOCKER_IMAGE_NAME)
                if 'settings' in config:
                    settings = config['settings']
                    if 'port' in settings:
                        port = settings['port']
                        self.PORT_CUBISM = port.get('port_http', self.PORT_CUBISM)
                        self.PORT_WEBSOCKET = port.get('port_websocket', self.PORT_WEBSOCKET)
                        self.PORT_MCP = port.get('port_mcp', self.PORT_MCP)
                    if 'authentication' in settings:
                        authentication = settings['authentication']
                        self.AUTH_TOKEN = str(authentication.get('token', self.AUTH_TOKEN)).lower()
                        self.REQUIRE_AUTH = False if self.AUTH_TOKEN == "" else True
                    if 'output' in settings:
                        self.OUTPUT_YAML = settings.get('output_yaml', self.OUTPUT_YAML)

        # File not found or YAML parsing error
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
        # YAML parsing error
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML configuration: {e}")
            sys.exit(1)
        # Other unexpected errors
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            sys.exit(1)

    def apply_args(self, args):
        """Apply command-line arguments to configuration."""
        if hasattr(args, 'workspace'):
            if args.workspace is not None:
                self.WORKSPACE = Path(args.workspace).resolve().absolute()
        if hasattr(args, 'output_yaml'):
            self.OUTPUT_YAML = args.output_yaml
        if hasattr(args, 'docker_file'):
            if args.docker_file is not None:
                path = self._path(args.docker_file)
                self.DOCKER_FILE_NAME = path if path is not None else self.DOCKER_FILE_NAME
        if hasattr(args, 'sdk_archive'):
            if args.sdk_archive is not None:
                path = self._path(args.sdk_archive)
                self.SDK_ARCHIVE = path if path is not None else self.SDK_ARCHIVE
        if hasattr(args, 'moc3_file'):
            if args.moc3_file is not None:
                path = self._path(args.moc3_file)
                self.MOC3_FILE = path if path is not None else self.MOC3_FILE
        if hasattr(args, 'code_directory'):
            if args.code_directory is not None:
                path = self._path(args.code_directory)
                self.CODE_DIRECTORY = path if path is not None else self.CODE_DIRECTORY
        if hasattr(args, 'docker_image_name'):
            if args.docker_image_name is not None:
                self.DOCKER_IMAGE_NAME = args.docker_image_name
        if hasattr(args, 'docker_container_name'):
            if args.docker_container_name is not None:
                self.DOCKER_CONTAINER_NAME = args.docker_container_name
        if hasattr(args, 'port_http'):
            if args.port_http is not None:
                self.PORT_CUBISM = args.port_http
        if hasattr(args, 'port_websocket'):
            if args.port_websocket is not None:
                self.PORT_WEBSOCKET = args.port_websocket
        if hasattr(args, 'port_mcp'):
            if args.port_mcp is not None:
                self.PORT_MCP = args.port_mcp
        if hasattr(args, 'production'):
            if args.production is not None:
                self.PRODUCTION = args.production
        if hasattr(args, 'token'):
            if args.token is not None:
                self.AUTH_TOKEN = str(args.token).lower()
                self.REQUIRE_AUTH = False if self.AUTH_TOKEN == "" else True
        if self.SDK_ARCHIVE is not None:
            if self.SDK_ARCHIVE.exists() and self.SDK_ARCHIVE.is_file():
                self.DOCKER_IMAGE_VER = self.SDK_ARCHIVE.stem
        if hasattr(args, 'docker_image_version'):
            if args.docker_image_version is not None:
                self.DOCKER_IMAGE_VER = args.docker_image_version


# ============================================================================
# Function
# ============================================================================
def _run_command(cmd, shell=True, capture_output=False, check=False):
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


def _remove_directory_and_empty_parents(work_dir, directory, max_depth=2):
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


def _ensure_container_running(config: ConfigActingDoll):
    """Check if container is running, start it if not."""
    # Check if container is running
    check_cmd = (
        f'docker ps --filter "name={config.DOCKER_CONTAINER_NAME}" '
        f'--format "{{{{.ID}}}}"'
    )
    result = _run_command(check_cmd, capture_output=True)

    if result.stdout.strip():
        # Container is running
        logger.info(f"Container {config.DOCKER_CONTAINER_NAME} is already running")
        return True

    # Check if container exists but is not running
    check_all_cmd = (
        f'docker ps -a --filter "name={config.DOCKER_CONTAINER_NAME}" '
        f'--format "{{{{.ID}}}}"'
    )
    result = _run_command(check_all_cmd, capture_output=True)

    if result.stdout.strip():
        # Container exists but is not running, start it
        logger.info(f"# Starting container {config.DOCKER_CONTAINER_NAME}...")
        result = _run_command(
            f"docker start {config.DOCKER_CONTAINER_NAME}", capture_output=True)
        if result.returncode != 0:
            logger.error(f"Failed to start container {config.DOCKER_CONTAINER_NAME}")
            logger.error("Please run create first.")
            return False
        logger.info(f"Container {config.DOCKER_CONTAINER_NAME} started successfully")
        return True
    else:
        # Container doesn't exist
        logger.error(f"Container {config.DOCKER_CONTAINER_NAME} does not exist")
        logger.error("Please run create first.")
        return False


def _docker_clean(config: ConfigActingDoll, with_image=False):
    """Delete Docker container and image."""
    # Remove existing containers
    logger.info("# Checking for existing containers...")
    ps_cmd = f'docker ps -a --format "{{{{.ID}}}}" --filter "ancestor={config.DOCKER_IMAGE_NAME}:{config.DOCKER_IMAGE_VER}"'
    result = _run_command(ps_cmd, capture_output=True)
    if result.stdout.strip():
        container_ids = result.stdout.strip().split('\n')
        for container_id in container_ids:
            logger.info(f"  - Removing container: {container_id}")
            _run_command(f"docker rm -f {container_id}", capture_output=True)

    if with_image:
        logger.info("# Checking for existing images...")
        img_cmd = f"docker image ls -q {config.DOCKER_IMAGE_NAME}:{config.DOCKER_IMAGE_VER}"
        result = _run_command(img_cmd, capture_output=True)
        if result.stdout.strip():
            logger.info(
                f"  - Remove existing image: {config.DOCKER_IMAGE_NAME}:{config.DOCKER_IMAGE_VER}")
            _run_command(
                f"docker rmi {config.DOCKER_IMAGE_NAME}:{config.DOCKER_IMAGE_VER}", capture_output=True)


def _docker_logs(config: ConfigActingDoll):
    """Display Docker container and image logs."""
    # Display existing containers
    try:
        logger.info("# Checking for existing containers...")
        ps_cmd = f'docker logs {config.DOCKER_CONTAINER_NAME}'
        _run_command(ps_cmd)
    except Exception as e:
        logger.error(f"Failed to retrieve container logs: {e}")


def _docker_restart(config: ConfigActingDoll):
    """Restart Docker container."""
    try:
        logger.info(f"# Restarting container {config.DOCKER_CONTAINER_NAME}...")
        _run_command(f"docker restart {config.DOCKER_CONTAINER_NAME}", capture_output=True)
        logger.info(f"Container {config.DOCKER_CONTAINER_NAME} restarted successfully")
    except Exception as e:
        logger.error(f"Failed to restart container {config.DOCKER_CONTAINER_NAME}: {e}")


# ============================================================================
# COMMAND
# ============================================================================
def cmd_docker_build(config: ConfigActingDoll):
    """Create Docker image and container."""

    # Display settings
    logger.info("=" * 50)
    logger.info("[Create Cubism SDK for Web Docker Container]")
    logger.info(f"  Code         : {config.CODE_DIRECTORY}")
    logger.info(f"  Docker")
    logger.info(f"    dockerfile : {config.DOCKER_FILE_NAME}")
    logger.info(f"    image      : {config.DOCKER_IMAGE_NAME}:{config.DOCKER_IMAGE_VER}")
    logger.info(f"    container  : {config.DOCKER_CONTAINER_NAME}")
    logger.info(f"      port(HTTP)      : {config.PORT_CUBISM}")
    logger.info(f"      port(Websocket) : {config.PORT_WEBSOCKET}")
    logger.info(f"      port(MCP)       : {config.PORT_MCP}")
    logger.info(f"  Cubism SDK for Web")
    logger.info(f"    archive   : {config.SDK_ARCHIVE}")
    logger.info(f"    moc3 file : {config.MOC3_FILE}")
    logger.info("=" * 50)

    # Check Files and Directories
    def _check_path(path, description):
        if path is None:
            logger.error(f"{description} path is not set.")
            sys.exit(1)
        if not path.exists():
            logger.error(f"{description} not found: {path}")
            sys.exit(1)

    logger.info(f"# Checking Dockerfile: {config.DOCKER_FILE_NAME}")
    _check_path(config.DOCKER_FILE_NAME, "Dockerfile")
    _check_path(config.CODE_DIRECTORY, "Code directory")
    _check_path(config.SDK_ARCHIVE, "SDK archive")
    _check_path(config.MOC3_FILE, "Moc3 file")

    # Remove existing containers
    _docker_clean(config, with_image=True)

    # Temporarily copy Core files to Dockerfile directory
    temp_root_dir = config.DOCKER_FILE_NAME.parent / 'temp_adapter'
    temp_resources_dir = temp_root_dir / "Resources"
    logger.info(f"# Copying files to {temp_root_dir} ...")
    try:
        _remove_directory_and_empty_parents(config.WORKSPACE, temp_root_dir)
        temp_root_dir.mkdir(parents=True, exist_ok=True)
        temp_resources_dir.mkdir(parents=True, exist_ok=True)
        # Source code directory
        shutil.copytree(config.CODE_DIRECTORY, temp_root_dir / config.CODE_DIRECTORY.name)
        _remove_directory_and_empty_parents(temp_root_dir, temp_root_dir / "adapter" / "acting_doll" / "public")
        _remove_directory_and_empty_parents(temp_root_dir, temp_root_dir / "adapter" / "acting_doll" / "dist")
        _remove_directory_and_empty_parents(temp_root_dir, temp_root_dir / "adapter" / "acting_doll" / "node_modules")
        _remove_directory_and_empty_parents(temp_root_dir, temp_root_dir / "adapter" / "acting_doll" / "public")
        # Cubism SDK for Web.zip
        shutil.copyfile(config.SDK_ARCHIVE, temp_root_dir / config.SDK_ARCHIVE.name)
        # Moc3 file and its parent directories
        shutil.copytree(config.MOC3_FILE.parent, temp_resources_dir / config.MOC3_FILE.parent.name)
    except Exception as e:
        logger.error(f"Failed to copy files: {e}")
        _remove_directory_and_empty_parents(config.WORKSPACE, temp_root_dir)
        sys.exit(1)

    # Build Docker image
    logger.info("# Building Docker image...")
    try:
        ref_dir = temp_root_dir.relative_to(config.WORKSPACE).as_posix()
        build_cmd = "docker build" \
            + f" --build-arg ADAPTER_DIR=./{ref_dir}" \
            + f" --build-arg SDK_ARCHIVE={config.SDK_ARCHIVE.stem}" \
            + f" -t {config.DOCKER_IMAGE_NAME}:{config.DOCKER_IMAGE_VER}" \
            + f" -f {str(config.DOCKER_FILE_NAME)}" \
            + f" {config.WORKSPACE}"
        result = _run_command(build_cmd, shell=False, check=True)
        if result.returncode != 0:
            logger.error(f"Failed to build Docker image")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to build Docker image: {e}")
        sys.exit(1)
    finally:
        # Clean up temporary files
        logger.info("# Cleaning up temporary files...")
        _remove_directory_and_empty_parents(config.WORKSPACE, temp_root_dir)

    # Verify Docker image
    img_list_cmd = f"docker image ls -q {config.DOCKER_IMAGE_NAME}:{config.DOCKER_IMAGE_VER}"
    result = _run_command(img_list_cmd, shell=True, capture_output=True)
    if result.returncode != 0:
        logger.error("[Error] Docker image setup failed! --")
        sys.exit(1)
    else:
        logger.info(f"# Docker Images list: {result.stdout.strip()}")


def cmd_docker_run(config: ConfigActingDoll, hosting: bool = False):
    """`docker run` command to start the container with appropriate volume mounts, port mappings, and environment variables."""
    # Run container
    try:
        logger.info("# Creating Docker container...")
        run_cmd = "docker container run -dit" \
            + f" --name {config.DOCKER_CONTAINER_NAME}" \
            + (f" -v {config.CODE_DIRECTORY}:/root/workspace/adapter:rw" if hosting else "") \
            + f" -p {config.PORT_CUBISM}:{config.PORT_CUBISM}" \
            + f" -p {config.PORT_WEBSOCKET}:{config.PORT_WEBSOCKET}" \
            + f" -p {config.PORT_MCP}:{config.PORT_MCP}" \
            + f" -e PORT_HTTP_NUMBER={config.PORT_CUBISM}" \
            + f" -e PORT_WEBSOCKET_NUMBER={config.PORT_WEBSOCKET}" \
            + f" -e PORT_MCP_NUMBER={config.PORT_MCP}" \
            + f" -e WEBSOCKET_AUTH_TOKEN={config.AUTH_TOKEN}" \
            + f" -e WEBSOCKET_REQUIRE_AUTH={config.REQUIRE_AUTH}" \
            + f" -e WEBSOCKET_ALLOWED_DIRS={':'.join(config.ALLOWED_DIRS)}" \
            + f" {config.DOCKER_IMAGE_NAME}:{config.DOCKER_IMAGE_VER}"
        result = _run_command(run_cmd, shell=False, capture_output=True)
        if result.returncode != 0:
            logger.error(f"Failed to start Docker container: {result.stderr}")
            sys.exit(1)
        else:
            logger.info("# -- Container setup completed successfully! --")
    except Exception as e:
        logger.error(f"Failed to start Docker container: {e}")
        sys.exit(1)
    if not hosting:
        try:
            logger.info("# Copying Cubism SDK files from container...")
            cubism_dir = config.CODE_DIRECTORY / 'Cubism'
            _remove_directory_and_empty_parents(config.WORKSPACE, cubism_dir)
            cp_cubism_cmd = "docker cp" \
                + f" {config.DOCKER_CONTAINER_NAME}:/root/workspace/adapter/Cubism" \
                + f" {cubism_dir}"
            result = _run_command(cp_cubism_cmd, shell=False, capture_output=True)
            if result.returncode != 0:
                logger.error(f"Failed to copy Cubism SDK files from container: {result.stderr}")
                sys.exit(1)
            else:
                logger.info("# -- Container setup completed successfully! --")
        except Exception as e:
            logger.error(f"Failed to copy Cubism SDK files from container: {e}")
            sys.exit(1)

    # Display running containers
    ps_filter_cmd = (
        f'docker ps -a --filter "ancestor={config.DOCKER_IMAGE_NAME}:{config.DOCKER_IMAGE_VER}" '
        f'--format "table {{{{.ID}}}}\\t{{{{.Names}}}}\\t{{{{.Image}}}}\\t{{{{.Status}}}}\\t{{{{.Ports}}}}"'
    )
    logger.info("=" * 50)
    logger.info("Docker Containers list:")
    result = _run_command(ps_filter_cmd, shell=True, capture_output=False)
    if result.returncode != 0:
        logger.error("[Error] Docker container setup failed!")
        sys.exit(1)


def cmd_rebuild(config: ConfigActingDoll,
                is_production: bool = True,
                build_node: bool = True,
                build_mcp: bool = True):
    """Build project inside Docker container."""
    # Ensure container is running
    if not _ensure_container_running(config):
        sys.exit(1)

    try:
        logger.info("# Rebuilding project inside Docker container...")
        cmd_rebuild = (
            f'docker exec -t'
            f' -e PRODUCTION={"true" if is_production else "false"}'
            f' -e BUILD_NODE={"true" if build_node else "false"}'
            f' -e BUILD_MCP={"true" if build_mcp else "false"}'
            f' {config.DOCKER_CONTAINER_NAME} /bin/sh -c "cd {config.root_dir};/bin/sh build.sh"'
        )
        result = _run_command(cmd_rebuild, check=True)
        if result.returncode != 0:
            logger.error(f"Build failed.")
            sys.exit(1)
        else:
            logger.info(f"Build completed successfully!")
    except Exception as e:
        logger.error(f"Failed to rebuild project inside Docker container: {e}")
        sys.exit(1)


def cmd_template(config: ConfigActingDoll, file_name: str = "config.yaml.template", output_dir: str = None):
    """Generate template files for Dockerfile and config.yaml."""
    try:
        output: Path = Path(output_dir).resolve().absolute() if output_dir is not None else config.WORKSPACE

        # Ensure output directory exists
        output.mkdir(parents=True, exist_ok=True)

        # Write config.yaml template
        config_path = output / file_name
        try:
            yaml_template = config.yaml_str()
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(yaml_template)
        except Exception as e:
            logger.error(f"Failed to write config.yaml template: {e}")
            sys.exit(1)

        logger.info("=" * 50)
        logger.info("[Generate Template Files]")
        logger.info(f"Generated: {config_path}")
    except Exception as e:
        logger.error(f"An error occurred while generating template files: {e}")
        sys.exit(1)


def cmd_exec(config: ConfigActingDoll):
    """Execute shell inside Docker container."""

    # Ensure container is running
    if not _ensure_container_running(config):
        # Show running containers
        logger.info("=" * 50)
        logger.info("[Docker Containers Running]")
        ps_filter_cmd = (
            f'docker ps -a --filter "ancestor={config.DOCKER_IMAGE_NAME}:{config.DOCKER_IMAGE_VER}" '
            f'--format "table {{{{.ID}}}}\\t{{{{.Image}}}}\\t{{{{.Status}}}}\\t{{{{.Names}}}}\\t{{{{.Ports}}}}"'
        )
        _run_command(ps_filter_cmd)
        return

    # Run npm start inside container
    logger.info("# Executing shell inside the container...")
    try:
        npm_cmd = f'docker exec -it {config.DOCKER_CONTAINER_NAME} /bin/sh'
        # Run the command and show output in real-time
        subprocess.run(npm_cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        # logger.error(f"[Error] executing shell: {e}")
        pass
    except KeyboardInterrupt:
        logger.info("# Shutting down...")


def cmd_stop_server(config: ConfigActingDoll):
    """Stop the server inside Docker container."""
    # Ensure container is running
    if not _ensure_container_running(config):
        sys.exit(1)

    try:
        logger.info("# Stopping server inside Docker container...")
        cmd_stop = (
            f'docker exec -t'
            f' -e SCRIPT_RUNNING="false"'
            f' {config.DOCKER_CONTAINER_NAME} /bin/sh -c "cd {config.root_dir};/bin/sh build.sh"'
        )
        result = _run_command(cmd_stop, check=True)
        if result.returncode != 0:
            logger.error(f"Build failed.")
            sys.exit(1)
        else:
            logger.info(f"Build completed successfully!")
    except Exception as e:
        logger.error(f"Failed to rebuild project inside Docker container: {e}")
        sys.exit(1)


# ============================================================================
# MAIN
# ============================================================================
def main():
    """Main entry point."""
    try:
        parser = argparse.ArgumentParser(
            description="Unified Docker container management for Cubism SDK Web"
        )

        subparsers = parser.add_subparsers(dest='command', help='Commands')

        # create command
        create_parser = subparsers.add_parser(
            'create',
            help='Create Docker image and container'
        )
        create_parser.add_argument(
            '-c', '--config',
            type=str,
            default=None,
            help='Path to config.yaml'
        )
        create_parser.add_argument(
            '-w', '--workspace',
            type=str,
            default=Path(__file__).parent.resolve(),
            help='Path to workspace folder (default: current folder)'
        )
        create_parser.add_argument(
            '--sdk_archive',
            type=str,
            default=None,
            help='Path to SDK zip file(required)'
        )
        create_parser.add_argument(
            '--moc3_file',
            type=str,
            default=None,
            help='Path to moc3 file(required)'
        )
        create_parser.add_argument(
            '--code_directory',
            type=str,
            default=None,
            help='Path to source code directory(required)'
        )

        create_parser.add_argument(
            '--docker_image_name',
            type=str,
            default='image_acting_doll',
            help='Name of the Docker image (default: image_acting_doll)'
        )
        create_parser.add_argument(
            '--docker_container_name',
            type=str,
            default=None,
            help='Name of the Docker container'
        )
        create_parser.add_argument(
            '--port_http',
            type=int,
            default=None,
            help='Port for HTTP server'
        )
        create_parser.add_argument(
            '--port_websocket',
            type=int,
            default=None,
            help='Port for WebSocket server'
        )
        create_parser.add_argument(
            '--port_mcp',
            type=int,
            default=None,
            help='Port for MCP server'
        )
        create_parser.add_argument(
            '--token',
            type=str,
            default='',
            help='Authentication token for WebSocket connections (default: empty, no authentication)'
        )
        create_parser.add_argument(
            '--output_yaml',
            action='store_true',
            default=True,
            help='Output configuration to YAML file'
        )

        # build command
        build_parser = subparsers.add_parser(
            'rebuild',
            help='Build project inside Docker container'
        )
        build_parser.add_argument(
            '-c', '--config',
            type=str,
            default=None,
            help='Path to config.yaml'
        )
        build_parser.add_argument(
            '-d', '--development',
            action='store_true',
            default=False,
            help='Build in development mode (npm run build)'
        )
        build_parser.add_argument(
            '--no_build_node_modules',
            action='store_true',
            default=False,
            help='Do not build node_modules (skip npm install)'
        )
        build_parser.add_argument(
            '--no_build_mcp',
            action='store_true',
            default=False,
            help='Do not build MCP (skip MCP build)'
        )

        # template command
        template_parser = subparsers.add_parser(
            'template',
            help='Generate template files for Dockerfile and config.yaml'
        )
        template_parser.add_argument(
            '-o', '--output',
            type=str,
            default=None,
            help='Output directory for template files (default: workspace root)'
        )
        # exec command
        exec_parser = subparsers.add_parser(
            'exec',
            help='Execute shell inside Docker container'
        )
        exec_parser.add_argument(
            '-c', '--config',
            type=str,
            default=None,
            help='Path to config.yaml'
        )
        # stop_server command
        stop_parser = subparsers.add_parser(
            'stop_server',
            help='Stop Server Script'
        )
        stop_parser.add_argument(
            '-c', '--config',
            type=str,
            default=None,
            help='Path to config.yaml'
        )

        ############################
        # parse arguments
        ############################
        args = parser.parse_args()

        if not args.command:
            parser.print_help()
            sys.exit(0)

        def _working_directory(path_str: str = None) -> Path:
            try:
                if path_str is not None and path_str != "":
                    work_dir = Path(path_str).resolve().absolute()
                else:
                    work_dir = Path(__file__).parent.resolve().absolute()
            except Exception as e:
                work_dir = Path(__file__).parent.resolve().absolute()
            # logger.info(f"Working directory set to: {work_dir}")
            os.chdir(work_dir)
            return work_dir

        # Load configuration
        if hasattr(args, 'workspace'):
            work_dir = _working_directory(args.workspace)
        else:
            work_dir = _working_directory()
        config: ConfigActingDoll = ConfigActingDoll(_working_directory(work_dir))

        # Load from YAML
        if hasattr(args, 'config'):
            config.load_from_yaml(args.config)
        config.apply_args(args)

        # Execute command
        if args.command == 'create':
            cmd_docker_build(config)
            cmd_docker_run(config, hosting=False)
            if config.VOLUME_SHARE:
                _docker_clean(config, with_image=False)
                cmd_docker_run(config, hosting=True)
            if config.OUTPUT_YAML:
                cmd_template(config,
                             file_name=f"{config.DOCKER_CONTAINER_NAME}.yaml",
                             output_dir=config.WORKSPACE / "config")
            # _docker_logs(config)
            logger.info("=" * 50)
            logger.info("\t(HTTP)\thttp://localhost:{port}".format(port=config.PORT_CUBISM))
            logger.info("\t(MCP)\thttp://localhost:{port}/sse".format(port=config.PORT_MCP))
        elif args.command == 'rebuild':
            development: bool = args.development if hasattr(args, 'development') else False
            build_node: bool = not args.no_build_node_modules if hasattr(
                args, 'no_build_node_modules') else True
            build_mcp: bool = not args.no_build_mcp if hasattr(args, 'no_build_mcp') else True
            cmd_rebuild(config, not development, build_node, build_mcp)
            _docker_restart(config)
        elif args.command == 'template':
            cmd_template(config, output_dir=args.output if hasattr(args, 'output') else None)
        elif args.command == 'exec':
            cmd_exec(config)
        elif args.command == 'stop_server':
            cmd_stop_server(config)
        else:
            parser.print_help()
            raise ValueError(f"Unknown command: {args.command}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
