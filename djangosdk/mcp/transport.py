from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TransportType(str, Enum):
    HTTP = "http"
    SSE = "sse"
    STDIO = "stdio"


@dataclass
class MCPTransportConfig:
    """Configuration for an MCP transport."""

    type: TransportType
    url: str | None = None          # HTTP / SSE
    command: str | None = None      # STDIO
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "MCPTransportConfig":
        if "command" in data:
            return cls(
                type=TransportType.STDIO,
                command=data["command"],
                args=data.get("args", []),
                env=data.get("env", {}),
            )
        transport_type = TransportType(data.get("transport", "http"))
        return cls(
            type=transport_type,
            url=data.get("url"),
            headers=data.get("headers", {}),
        )


class StdioTransport:
    """Communicates with an MCP server over stdin/stdout."""

    def __init__(self, config: MCPTransportConfig) -> None:
        self._config = config
        self._process: subprocess.Popen | None = None

    def start(self) -> None:
        import os

        env = dict(os.environ, **self._config.env)
        self._process = subprocess.Popen(
            [self._config.command, *self._config.args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True,
        )

    def send(self, message: dict) -> dict:
        if not self._process or self._process.poll() is not None:
            self.start()
        line = json.dumps(message) + "\n"
        self._process.stdin.write(line)
        self._process.stdin.flush()
        response_line = self._process.stdout.readline()
        return json.loads(response_line)

    def stop(self) -> None:
        if self._process:
            self._process.terminate()
            self._process = None


class HttpTransport:
    """Communicates with an MCP server over HTTP."""

    def __init__(self, config: MCPTransportConfig) -> None:
        self._config = config

    def send(self, message: dict) -> dict:
        try:
            import urllib.request

            data = json.dumps(message).encode()
            req = urllib.request.Request(
                self._config.url,
                data=data,
                headers={
                    "Content-Type": "application/json",
                    **self._config.headers,
                },
            )
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode())
        except Exception as exc:
            raise RuntimeError(
                f"MCP HTTP transport error: {exc}"
            ) from exc


def build_transport(config: MCPTransportConfig) -> Any:
    if config.type == TransportType.STDIO:
        return StdioTransport(config)
    return HttpTransport(config)
