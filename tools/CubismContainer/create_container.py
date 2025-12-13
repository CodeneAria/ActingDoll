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
import shutil


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
    os.chdir(script_dir)
    config_path = script_dir / "config.yaml"

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print(
            f"[Error] Configuration file not found: {config_path}", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as e:
        print(
            f"[Error] Failed to parse YAML configuration: {e}", file=sys.stderr)
        sys.exit(1)

    DOCKER_FILE_NAME = config['docker']['dockerfile']
    DOCKER_IMAGE_NAME = config['docker']['image']['name']
    DOCKER_IMAGE_VER = config['docker']['image']['version']
    DOCKER_CONTAINER_NAME = config['docker']['container']['name']
    SERVER_PORT = config['docker']['container']['port']
    GIT_FRAMEWORK_REPO = config['cubism']['git_framework_repo']
    GIT_FRAMEWORK_TAG = config['cubism']['git_framework_tag']
    GIT_FRAMEWORK_DIR_NAME = config['cubism']['git_framework_dir_name']
    GIT_SAMPLE_REPO = config['cubism']['git_sample_repo']
    GIT_SAMPLE_TAG = config['cubism']['git_sample_tag']
    GIT_SAMPLE_DIR_NAME = config['cubism']['git_sample_dir_name']
    ARCHIVE_CORE_DIR = config['cubism']['archive_core_dir']
    CONTROLS_DIR = config['custom']['controls_dir']
    NODE_PACKAGE_DIR = config['custom']['node_package_dir']
    MODELS_DIR = config['custom']['models_dir']

    archive_core_path = Path(ARCHIVE_CORE_DIR).absolute()
    dockerfile_path = Path(script_dir / DOCKER_FILE_NAME).absolute()
    node_package_dir = Path(NODE_PACKAGE_DIR).absolute()
    controls_path = Path(CONTROLS_DIR).absolute()
    models_path = Path(MODELS_DIR).absolute()

    # Display settings
    print("=" * 50)
    print("[Create Cubism SDK for Web Docker Container]")
    print(f"  Git")
    print(f"    Framework      : {GIT_FRAMEWORK_REPO}[{GIT_FRAMEWORK_TAG}]")
    print(f"    Sample         : {GIT_SAMPLE_REPO}[{GIT_SAMPLE_TAG}]")
    print(f"  PATH             : {script_dir}")
    print(f"  Archive Core dir : {archive_core_path}")
    print(f"  dockerfile       : {dockerfile_path}")
    print(f"  Docker image     : {DOCKER_IMAGE_NAME}:{DOCKER_IMAGE_VER}")
    print(f"  Docker container : {DOCKER_CONTAINER_NAME}")
    print(f"      port         : {SERVER_PORT}")
    print("=" * 50)

    # Check Cubism Core files
    print(f"# Checking {archive_core_path}...")
    if not archive_core_path.exists():
        print(
            f"[Error] Archive core directory not found: {archive_core_path}", file=sys.stderr)
        sys.exit(1)
    js_files = list(archive_core_path.glob("*core*"))
    if not js_files:
        print(
            f"[Error] Cubism Core file not found: {archive_core_path}", file=sys.stderr)
        print("Please download it from https://www.live2d.com/sdk/download/web/", file=sys.stderr)
        sys.exit(1)

    # Remove existing containers
    print("# Checking for existing containers...")
    ps_cmd = f'docker ps -a --format "{{{{.ID}}}}" --filter "ancestor={DOCKER_IMAGE_NAME}:{DOCKER_IMAGE_VER}"'
    result = run_command(ps_cmd, capture_output=True)
    if result.stdout.strip():
        container_ids = result.stdout.strip().split('\n')
        for container_id in container_ids:
            print(f"## Remove existing container: ID[{container_id}]")
            run_command(f"docker stop {container_id}", capture_output=True)
            run_command(f"docker rm {container_id}", capture_output=True)

    # Remove existing image
    print("# Checking for existing images...")
    img_cmd = f"docker image ls -q {DOCKER_IMAGE_NAME}:{DOCKER_IMAGE_VER}"
    result = run_command(img_cmd, capture_output=True)
    if result.stdout.strip():
        print(
            f"## Remove existing image: {DOCKER_IMAGE_NAME}:{DOCKER_IMAGE_VER}")
        run_command(
            f"docker rmi {DOCKER_IMAGE_NAME}:{DOCKER_IMAGE_VER}", capture_output=True)

    # Build Docker image
    print("# Building Docker image...")
    build_cmd = [
        "docker", "build",
        "--build-arg", f"CORE_ARCHIVE_DIR={ARCHIVE_CORE_DIR}",
        "--build-arg", f"GIT_FRAMEWORK_REPO={GIT_FRAMEWORK_REPO}",
        "--build-arg", f"GIT_FRAMEWORK_TAG={GIT_FRAMEWORK_TAG}",
        "--build-arg", f"GIT_FRAMEWORK_DIR_NAME={GIT_FRAMEWORK_DIR_NAME}",
        "--build-arg", f"GIT_SAMPLE_REPO={GIT_SAMPLE_REPO}",
        "--build-arg", f"GIT_SAMPLE_TAG={GIT_SAMPLE_TAG}",
        "--build-arg", f"GIT_SAMPLE_DIR_NAME={GIT_SAMPLE_DIR_NAME}",
        "-t", f"{DOCKER_IMAGE_NAME}:{DOCKER_IMAGE_VER}",
        "-f", str(dockerfile_path),
        "."
    ]
    try:
        run_command(build_cmd, shell=False, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[Error] Failed to build Docker image", file=sys.stderr)
        sys.exit(1)

    # Run container
    run_cmd = [
        "docker", "container", "run",
        "--name", DOCKER_CONTAINER_NAME,
        "-dit",
        "-v", f"{models_path}:/root/workspace/Cubism/models",
        "-v", f"{controls_path}:/root/workspace/Cubism/adapter",
        "-p", f"{SERVER_PORT}:5000",
        f"{DOCKER_IMAGE_NAME}:{DOCKER_IMAGE_VER}"
    ]
    result = run_command(run_cmd, shell=False, capture_output=True)
    if result.returncode != 0:
        print(f"[Error] Failed to start Docker container", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)

    # Copy custom node package
    print("# Copying custom node package...")
    build_cmd = [
        "docker", "cp",
        str(node_package_dir) + "/",
        f"{DOCKER_CONTAINER_NAME}:{'/root/workspace/Cubism/'}"
    ]
    try:
        run_command(build_cmd, shell=False, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[Error] Failed to build Docker image", file=sys.stderr)
        sys.exit(1)

    print("\n# -- Container setup completed successfully! --")


if __name__ == "__main__":
    main()
