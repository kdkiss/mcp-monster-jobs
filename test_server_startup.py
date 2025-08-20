#!/usr/bin/env python3
"""
Test script to verify server startup and basic functionality
"""

import subprocess
import sys
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test-server")

def test_docker_build():
    """Test Docker image build"""
    logger.info("Testing Docker image build...")
    try:
        result = subprocess.run(
            ["docker", "build", "-t", "monster-server", "."],
            capture_output=True,
            text=True,
            timeout=600
        )
        if result.returncode == 0:
            logger.info("Docker build successful")
            return True
        else:
            logger.error(f"Docker build failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        logger.error("Docker build timed out")
        return False
    except Exception as e:
        logger.error(f"Error testing Docker build: {e}")
        return False

def test_docker_run():
    """Test running the server in Docker"""
    logger.info("Testing Docker container startup...")
    try:
        # Run the container in detached mode
        run_result = subprocess.run(
            ["docker", "run", "-d", "-i", "--name", "monster-test", "monster-server"],
            capture_output=True,
            text=True,
            timeout=30
        )

        if run_result.returncode != 0:
            logger.error(f"Failed to start Docker container: {run_result.stderr}")
            return False

        # Check container logs
        time.sleep(5)  # Give the server time to start
        logs_result = subprocess.run(
            ["docker", "logs", "monster-test"],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Check if container is running
        ps_result = subprocess.run(
            ["docker", "ps", "-a", "--filter", "name=monster-test", "--format", "{{.Status}}"],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Clean up
        subprocess.run(
            ["docker", "rm", "-f", "monster-test"],
            capture_output=True,
            text=True
        )

        logger.info(f"Container status: {ps_result.stdout.strip()}")
        logger.info(f"Container logs: {logs_result.stdout}")

        # Check if server started successfully
        if "Starting Monster MCP Server" in logs_result.stdout:
            logger.info("Server started successfully in Docker")
            return True
        else:
            logger.error("Server failed to start in Docker")
            return False
    except subprocess.TimeoutExpired:
        logger.error("Docker test timed out")
        return False
    except Exception as e:
        logger.error(f"Error testing Docker container: {e}")
        return False

def test_health_check_in_docker():
    """Test server health check in Docker"""
    logger.info("Testing server health check in Docker...")
    try:
        # Run a temporary container to check health
        result = subprocess.run(
            ["docker", "run", "--rm", "monster-server", "python", "monster_server.py", "--health"],
            capture_output=True,
            text=True,
            timeout=15
        )

        if result.returncode == 0 and "Server is healthy" in result.stdout:
            logger.info("Health check passed in Docker")
            return True
        else:
            logger.error(f"Health check failed in Docker: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        logger.error("Health check timed out in Docker")
        return False
    except Exception as e:
        logger.error(f"Error testing health check in Docker: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("Starting server verification tests...")

    # Test Docker build
    docker_success = test_docker_build()

    # Test health check in Docker
    health_success = test_health_check_in_docker()

    # Test Docker run
    run_success = test_docker_run()

    # Summary
    logger.info("\n=== Test Results ===")
    logger.info(f"Docker Build: {'PASS' if docker_success else 'FAIL'}")
    logger.info(f"Health Check in Docker: {'PASS' if health_success else 'FAIL'}")
    logger.info(f"Docker Run: {'PASS' if run_success else 'FAIL'}")

    if all([docker_success, health_success, run_success]):
        logger.info("All tests PASSED! Server is ready for deployment.")
        return 0
    else:
        logger.error("Some tests FAILED. Please check the logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())