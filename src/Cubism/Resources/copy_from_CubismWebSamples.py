#!/usr/bin/env python3
"""
Docker container copy resource from Cubism SDK for Web Samples
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

    DOCKER_IMAGE_NAME = config['docker']['image']['name']
    DOCKER_IMAGE_VER = config['docker']['image']['version']
    DOCKER_CONTAINER_NAME = config['docker']['container']['name']
    MODELS_DIR = config['cubism']['models_dir']

    models_path = Path(MODELS_DIR).parent.resolve().absolute()
    samples_resources_dir="/root/workspace/Cubism/Samples/Samples/Resources"

    print("=" * 50)
    print("[Copy model resources from Cubism SDK for Web container]")
    print(f"  src dir  : {DOCKER_CONTAINER_NAME}:{samples_resources_dir}")
    print(f"  dist dir : {models_path}")
    print("=" * 50)

    # Show running containers
    print("=" * 50)
    print("[Docker Containers Running]")
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
    npm_cmd = (
        f'docker cp {DOCKER_CONTAINER_NAME}:{samples_resources_dir} {models_path}'
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
    work_dir = Path(__file__).parent.parent.parent.parent.resolve()
    os.chdir(work_dir)
    config_path = Path("src").absolute() / "config.yaml"
    main(work_dir, config_path)
