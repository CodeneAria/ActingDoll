"""HTTP client for Live2D Cubism SDK web server."""

import httpx


class Live2DClient:
    """Client to communicate with Live2D Cubism SDK web server."""

    def __init__(self, base_url: str = "http://localhost:8080") -> None:
        """Initialize the Live2D client.

        Args:
            base_url: The base URL of the Live2D Cubism SDK web server.
        """
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=30.0)

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def set_parameter(self, parameter_id: str, value: float) -> dict:
        """Set a Live2D model parameter.

        Args:
            parameter_id: The ID of the parameter to set (e.g., "ParamAngleX", "ParamEyeLOpen").
            value: The value to set (typically -30 to 30 for angles, 0 to 1 for others).

        Returns:
            Response from the server.
        """
        response = await self._client.post(
            f"{self.base_url}/api/parameter",
            json={"parameterId": parameter_id, "value": value},
        )
        response.raise_for_status()
        return response.json()

    async def set_expression(self, expression_id: str) -> dict:
        """Set a Live2D model expression.

        Args:
            expression_id: The ID of the expression to set.

        Returns:
            Response from the server.
        """
        response = await self._client.post(
            f"{self.base_url}/api/expression",
            json={"expressionId": expression_id},
        )
        response.raise_for_status()
        return response.json()

    async def start_motion(self, group: str, index: int, priority: int = 2) -> dict:
        """Start a Live2D model motion.

        Args:
            group: The motion group name.
            index: The motion index within the group.
            priority: The motion priority (1=idle, 2=normal, 3=force).

        Returns:
            Response from the server.
        """
        response = await self._client.post(
            f"{self.base_url}/api/motion",
            json={"group": group, "index": index, "priority": priority},
        )
        response.raise_for_status()
        return response.json()

    async def get_model_info(self) -> dict:
        """Get information about the current Live2D model.

        Returns:
            Model information including available parameters, expressions, and motions.
        """
        response = await self._client.get(f"{self.base_url}/api/model")
        response.raise_for_status()
        return response.json()

    async def reset_pose(self) -> dict:
        """Reset the Live2D model to its default pose.

        Returns:
            Response from the server.
        """
        response = await self._client.post(f"{self.base_url}/api/reset")
        response.raise_for_status()
        return response.json()

    async def set_look_at(self, x: float, y: float) -> dict:
        """Set the look-at target for the Live2D model.

        Args:
            x: X coordinate (-1.0 to 1.0, left to right).
            y: Y coordinate (-1.0 to 1.0, bottom to top).

        Returns:
            Response from the server.
        """
        response = await self._client.post(
            f"{self.base_url}/api/lookat",
            json={"x": x, "y": y},
        )
        response.raise_for_status()
        return response.json()
