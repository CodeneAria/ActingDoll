#!/usr/bin/env python3
"""
Docker container creation script for Cubism SDK Web
"""

import os
import sys
import subprocess
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


def main(work_dir, config_path):
    # Load settings from YAML
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
    SERVER_PORT = config['docker']['container']['port_cubism']
    WEBSOCKET_PORT = config['docker']['container']['port_websocket']
    GIT_FRAMEWORK_REPO = config['cubism']['git_framework_repo']
    GIT_FRAMEWORK_TAG = config['cubism']['git_framework_tag']
    GIT_FRAMEWORK_DIR_NAME = config['cubism']['git_framework_dir_name']
    GIT_SAMPLE_REPO = config['cubism']['git_sample_repo']
    GIT_SAMPLE_TAG = config['cubism']['git_sample_tag']
    GIT_SAMPLE_DIR_NAME = config['cubism']['git_sample_dir_name']
    ARCHIVE_CORE_DIR = config['cubism']['archive_core_dir']
    MODELS_DIR = config['cubism']['models_dir']
    ADAPTER_DIR = config['custom']['adapter_dir']

    dockerfile_path = Path(work_dir / DOCKER_FILE_NAME).resolve().absolute()
    adapter_dir = Path(ADAPTER_DIR).resolve().absolute()
    archive_core_path = Path(ARCHIVE_CORE_DIR).resolve().absolute()
    models_path = Path(MODELS_DIR).resolve().absolute()
    temp_core_dir = Path(work_dir / "volume" / "Core").resolve().absolute()

    # Display settings
    print("=" * 50)
    print("[Create Cubism SDK for Web Docker Container]")
    print(f"  Git")
    print(f"    Framework : {GIT_FRAMEWORK_REPO}[{GIT_FRAMEWORK_TAG}]")
    print(f"    Sample    : {GIT_SAMPLE_REPO}[{GIT_SAMPLE_TAG}]")
    print(f"  Files")
    print(f"    Working Dir       : {work_dir}")
    print(f"    Config            : {config_path}")
    print(f"    Cubism Core Dir   : {archive_core_path}")
    print(f"    Cubism Models Dir : {models_path}")
    print(f"  Docker")
    print(f"    dockerfile : {dockerfile_path}")
    print(f"    image      : {DOCKER_IMAGE_NAME}:{DOCKER_IMAGE_VER}")
    print(f"    container  : {DOCKER_CONTAINER_NAME}")
    print(f"        port   : {SERVER_PORT}")
    print("=" * 50)

    # Check Cubism Core files
    print(f"# Checking Archive Core directory: {archive_core_path}")
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
            print(f"  - Remove existing container: ID[{container_id}]")
            run_command(f"docker stop {container_id}", capture_output=True)
            run_command(f"docker rm {container_id}", capture_output=True)

    # Remove existing image
    print("# Checking for existing images...")
    img_cmd = f"docker image ls -q {DOCKER_IMAGE_NAME}:{DOCKER_IMAGE_VER}"
    result = run_command(img_cmd, capture_output=True)
    if result.stdout.strip():
        print(
            f"  - Remove existing image: {DOCKER_IMAGE_NAME}:{DOCKER_IMAGE_VER}")
        run_command(
            f"docker rmi {DOCKER_IMAGE_NAME}:{DOCKER_IMAGE_VER}", capture_output=True)

    # Build Docker image
    print("# Building Docker image...")

    # Temporarily copy Core files to Dockerfile directory

    print(f"# Copying Core files to {temp_core_dir}")
    try:
        if temp_core_dir.exists():
            shutil.rmtree(temp_core_dir)
        shutil.copytree(archive_core_path, temp_core_dir)
    except Exception as e:
        print(f"[Error] Failed to copy Core files: {e}", file=sys.stderr)
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
            "-t", f"{DOCKER_IMAGE_NAME}:{DOCKER_IMAGE_VER}",
            "-f", str(dockerfile_path),
            "."
        ]
        run_command(build_cmd, shell=False, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[Error] Failed to build Docker image", file=sys.stderr)
        sys.exit(1)
    finally:
        # Clean up temporary Core files
        print("# Cleaning up temporary Core files...")
        if temp_core_dir.exists():
            shutil.rmtree(temp_core_dir)

    # Run container
    run_cmd = [
        "docker", "container", "run",
        "--name", DOCKER_CONTAINER_NAME,
        "-dit",
        "-v", f"{adapter_dir}:/root/workspace/adapter",
        "-v", f"{models_path}:/root/workspace/Cubism/Resources",
        "-p", f"{SERVER_PORT}:5000",
        "-p", f"{WEBSOCKET_PORT}:8765",
        f"{DOCKER_IMAGE_NAME}:{DOCKER_IMAGE_VER}"
    ]
    result = run_command(run_cmd, shell=False, capture_output=True)
    if result.returncode != 0:
        print(f"[Error] Failed to start Docker container", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)

    ps_filter_cmd = (
        f'docker ps --filter "ancestor={DOCKER_IMAGE_NAME}:{DOCKER_IMAGE_VER}" '
        f'--format "table {{{{.ID}}}}\\t{{{{.Image}}}}\\t{{{{.Status}}}}\\t{{{{.Names}}}}\\t{{{{.Ports}}}}"'
    )
    result = run_command(ps_filter_cmd, shell=False, capture_output=True)
    if result.returncode != 0:
        print("\n[Error] Container setup failed! --")
    else:
        print("\n# -- Container setup completed successfully! --")


if __name__ == "__main__":
    work_dir = Path(__file__).parent.parent.parent.resolve()
    os.chdir(work_dir)
    config_path = Path("src").resolve().absolute() / "config.yaml"
    main(work_dir, config_path)
