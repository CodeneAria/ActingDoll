#!/usr/bin/env python3
"""
Docker container creation script for Cubism SDK Web
"""

import os
import sys
import subprocess
import json
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
    except yaml.YAMLError as e:
        print(
            f"Error: Failed to parse YAML configuration: {e}", file=sys.stderr)
        sys.exit(1)

    DOCKER_FILE_NAME = config['docker']['dockerfile']
    DOCKER_IMAGE_NAME = config['docker']['image']['name']
    DOCKER_IMAGE_VER = config['docker']['image']['version']
    DOCKER_CONTAINER_NAME = config['docker']['container']['name']
    SERVER_PORT = config['docker']['container']['port']
    CUBISM_SDK_FOR_WEB_PATH = config['cubism']['sdk_zip_path']
    WORK_DIR = config['cubism']['work_dir']
    SHARD_DIR = config['cubism']['shared_dir']

    # Display settings
    print("=" * 50)
    print(f"  PATH             : {script_dir}")
    print(f"  dockerfile       : {DOCKER_FILE_NAME}")
    print(f"  Docker image     : {DOCKER_IMAGE_NAME}:{DOCKER_IMAGE_VER}")
    print(f"  Docker container : {DOCKER_CONTAINER_NAME}")
    print(f"      port         : {SERVER_PORT}")
    print("=" * 50)

    # Extract Cubism SDK
    print(f"Extracting {CUBISM_SDK_FOR_WEB_PATH}...")
    if not Path(CUBISM_SDK_FOR_WEB_PATH).exists():
        print(
            f"Error: Cubism SDK file not found: {CUBISM_SDK_FOR_WEB_PATH}", file=sys.stderr)
        print("Please download it from https://www.live2d.com/sdk/download/web/", file=sys.stderr)
        sys.exit(1)

    # Create work directory if it doesn't exist
    work_dir_path = Path(WORK_DIR)
    work_dir_path.mkdir(parents=True, exist_ok=True)
    print(f"Work directory: {work_dir_path.resolve()}")

    tar_cmd = f'tar -xf {CUBISM_SDK_FOR_WEB_PATH} -C "{WORK_DIR}" --strip-components=1'
    result = run_command(tar_cmd, check=False)
    if result.returncode != 0:
        print(f"Error: Failed to extract SDK archive", file=sys.stderr)
        sys.exit(1)

    # Remove existing containers
    print("Checking for existing containers...")
    ps_cmd = f'docker ps -a --format "{{{{.ID}}}}" --filter "ancestor={DOCKER_IMAGE_NAME}:{DOCKER_IMAGE_VER}"'
    result = run_command(ps_cmd, capture_output=True)

    if result.stdout.strip():
        container_ids = result.stdout.strip().split('\n')
        for container_id in container_ids:
            print(f"[INFO] Remove existing container: ID[{container_id}]")
            run_command(f"docker stop {container_id}", capture_output=True)
            run_command(f"docker rm {container_id}", capture_output=True)

    # Remove existing image
    print("Checking for existing images...")
    img_cmd = f"docker image ls -q {DOCKER_IMAGE_NAME}:{DOCKER_IMAGE_VER}"
    result = run_command(img_cmd, capture_output=True)

    if result.stdout.strip():
        print(
            f"[INFO] Remove existing image: {DOCKER_IMAGE_NAME}:{DOCKER_IMAGE_VER}")
        run_command(
            f"docker rmi {DOCKER_IMAGE_NAME}:{DOCKER_IMAGE_VER}", capture_output=True)

    # Build Docker image
    print("Building Docker image...")
    build_cmd = [
        "docker", "build",
        "--build-arg", f"SERVER_PORT={SERVER_PORT}",
        "-t", f"{DOCKER_IMAGE_NAME}:{DOCKER_IMAGE_VER}",
        "-f", str(script_dir / DOCKER_FILE_NAME),
        "."
    ]
    try:
        run_command(build_cmd, shell=False, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to build Docker image", file=sys.stderr)
        sys.exit(1)

    # Show images
    print("/" * 50)
    run_command("docker images")
    print("/" * 50)

    # Run container
    shard_dir_path = script_dir / SHARD_DIR
    run_cmd_display = (
        f"docker container run "
        f"--name {DOCKER_CONTAINER_NAME} -dit "
        f"-v {shard_dir_path}:/root/work "
        f"-p {SERVER_PORT}:5000 "
        f"{DOCKER_IMAGE_NAME}:{DOCKER_IMAGE_VER}"
    )
    print(run_cmd_display)
    print("/" * 50)

    run_cmd = [
        "docker", "container", "run",
        "--name", DOCKER_CONTAINER_NAME,
        "-dit",
        "-v", f"{shard_dir_path}:/root/work",
        "-p", f"{SERVER_PORT}:5000",
        f"{DOCKER_IMAGE_NAME}:{DOCKER_IMAGE_VER}"
    ]
    result = run_command(run_cmd, shell=False, capture_output=True)
    if result.returncode != 0:
        print(f"Error: Failed to start Docker container", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)

    # Inspect container
    run_command(f"docker container inspect {DOCKER_CONTAINER_NAME}")

    # Show running containers
    ps_filter_cmd = (
        f'docker ps --filter "ancestor={DOCKER_IMAGE_NAME}:{DOCKER_IMAGE_VER}" '
        f'--format "table {{{{.ID}}}}\\t{{{{.Image}}}}\\t{{{{.Status}}}}\\t{{{{.Names}}}}\\t{{{{.Ports}}}}"'
    )
    run_command(ps_filter_cmd)

    # Install and build inside container
    print("npm install and build inside the container...")
    npm_cmd = (
        f'docker exec -t {DOCKER_CONTAINER_NAME} '
        f'/bin/sh -c "cd /root/work/Samples/TypeScript/Demo && npm install -g npm && npm install && npm run build"'
    )
    try:
        run_command(npm_cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to install or build npm packages", file=sys.stderr)
        sys.exit(1)

    print("\nContainer setup completed successfully!")


if __name__ == "__main__":
    main()
