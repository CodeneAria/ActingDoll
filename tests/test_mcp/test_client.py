"""Tests for the Live2D client."""

import pytest

from acting_doll.client import Live2DClient


class TestLive2DClient:
    """Tests for Live2DClient."""

    def test_init_default_url(self) -> None:
        """Test that the client initializes with default URL."""
        client = Live2DClient()
        assert client.base_url == "http://localhost:5000"

    def test_init_custom_url(self) -> None:
        """Test that the client initializes with custom URL."""
        client = Live2DClient(base_url="http://localhost:9000")
        assert client.base_url == "http://localhost:9000"

    def test_init_strips_trailing_slash(self) -> None:
        """Test that trailing slash is removed from URL."""
        client = Live2DClient(base_url="http://localhost:5000/")
        assert client.base_url == "http://localhost:5000"

    @pytest.mark.asyncio
    async def test_close(self) -> None:
        """Test that the client can be closed."""
        client = Live2DClient()
        await client.close()
        # Should not raise any exception
