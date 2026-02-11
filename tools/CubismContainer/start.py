#!/usr/bin/env python3
"""
Docker container run script for Cubism SDK Web
"""

import os
import subprocess
import sys
import yaml
from pathlib import Path


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
        print(
            f"Error: Configuration file not found: {config_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: Failed to load configuration: {e}", file=sys.stderr)
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

    server_dir = f"/root/workspace/adapter/server"

    # Show running containers
    print("=" * 50)
    print("[Start Cubism SDK for Web]")
    ps_filter_cmd = (
        f'docker ps -a --filter "ancestor={DOCKER_IMAGE_NAME}:{DOCKER_IMAGE_VER}" '
        f'--format "table {{{{.ID}}}}\\t{{{{.Image}}}}\\t{{{{.Status}}}}\\t{{{{.Names}}}}\\t{{{{.Ports}}}}"'
    )
    run_command(ps_filter_cmd)
    print("=" * 50)

    # Restart container
    print(f"# Restarting container {DOCKER_CONTAINER_NAME}...")
    result = run_command(
        f"docker restart {DOCKER_CONTAINER_NAME}", capture_output=True)
    if result.returncode != 0:
        print(
            f"[Error] Failed to start container {DOCKER_CONTAINER_NAME}", file=sys.stderr)
        print("Please run create_container.py first.", file=sys.stderr)
        sys.exit(1)

    # Run npm start inside container
    print("# Running npm start...")
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
        print(f"[Error] running npm start: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n# Shutting down...")
        run_command(
            f"docker stop {DOCKER_CONTAINER_NAME}", capture_output=True)
        sys.exit(0)


if __name__ == "__main__":
    work_dir = Path(__file__).parent.parent.parent.resolve()
    os.chdir(work_dir)
    config_path = Path("src").resolve().absolute() / "config.yaml"
    main(work_dir, config_path)
