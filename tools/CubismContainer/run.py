#!/usr/bin/env python3
"""
Docker container run script for Cubism SDK Web
"""

import subprocess
import sys
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
    # Settings
    DOCKER_IMAGE_NAME = "img_node"
    DOCKER_IMAGE_VER = "latest"
    DOCKER_CONTAINER_NAME = "node_server"

    script_dir = Path(__file__).parent.resolve()

    # Display settings
    print("=" * 50)
    print("[Setup docker image]")
    print("=" * 50)
    print(f"  PATH             : {script_dir}")
    print(f"  Docker container : {DOCKER_CONTAINER_NAME}")
    print("=" * 50)

    # Show running containers
    ps_filter_cmd = (
        f'docker ps --filter "ancestor={DOCKER_IMAGE_NAME}:{DOCKER_IMAGE_VER}" '
        f'--format "table {{{{.ID}}}}\\t{{{{.Image}}}}\\t{{{{.Status}}}}\\t{{{{.Names}}}}\\t{{{{.Ports}}}}"'
    )
    run_command(ps_filter_cmd)

    # Start container
    print(f"\nStarting container {DOCKER_CONTAINER_NAME}...")
    run_command(f"docker start {DOCKER_CONTAINER_NAME}")

    # Run npm start inside container
    print("Running npm start inside the container...")
    npm_cmd = (
        f'docker exec -t {DOCKER_CONTAINER_NAME} '
        f'/bin/sh -c "cd /root/work/Samples/TypeScript/Demo && npm run start"'
    )

    try:
        # Run the command and show output in real-time
        subprocess.run(npm_cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running npm start: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)


if __name__ == "__main__":
    main()
