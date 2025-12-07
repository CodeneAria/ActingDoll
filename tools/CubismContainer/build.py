#!/usr/bin/env python3
"""
Docker container run script for Cubism SDK Web
"""

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


def main():
    # Load settings from YAML
    script_dir = Path(__file__).parent.resolve()
    config_path = script_dir / "config.yaml"

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

    DOCKER_IMAGE_NAME = config['docker']['image']['name']
    DOCKER_IMAGE_VER = config['docker']['image']['version']
    DOCKER_CONTAINER_NAME = config['docker']['container']['name']

    model_path = f"/root/work/model"

    # Show running containers
    print("=" * 50)
    print("[Build model inside Cubism SDK for Web container]")
    ps_filter_cmd = (
        f'docker ps --filter "ancestor={DOCKER_IMAGE_NAME}:{DOCKER_IMAGE_VER}" '
        f'--format "table {{{{.ID}}}}\\t{{{{.Image}}}}\\t{{{{.Status}}}}\\t{{{{.Names}}}}\\t{{{{.Ports}}}}"'
    )
    run_command(ps_filter_cmd)
    print("=" * 50)

    # Start container
    print(f"# Starting container {DOCKER_CONTAINER_NAME}...")
    result = run_command(
        f"docker start {DOCKER_CONTAINER_NAME}", capture_output=True)
    if result.returncode != 0:
        print(
            f"[Error] Failed to start container {DOCKER_CONTAINER_NAME}", file=sys.stderr)
        print("Please run create_container.py first.", file=sys.stderr)
        sys.exit(1)

    # Run npm start inside container
    print("# Running npm start inside the container...")
    # npm install -g npm && npm install && npm run build
    npm_cmd = (
        f'docker exec -t {DOCKER_CONTAINER_NAME} /bin/sh -c "'
        f'cd {model_path}'
        f' && npm install -g npm && npm install'
        f' && npm audit fix'
        f' && npm run build'
        f'"'
    )

    try:
        # Run the command and show output in real-time
        subprocess.run(npm_cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[Error] running npm start: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n# Shutting down...")
        sys.exit(0)


if __name__ == "__main__":
    main()
