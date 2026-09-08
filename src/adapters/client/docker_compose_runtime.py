from __future__ import annotations

import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

from ports.container_runtime import IContainerRuntime


class DockerComposeRuntime(IContainerRuntime):
    """Drives the spool container.

    Prefers the standalone `docker-compose` binary, because the compose plugin is frequently absent
    on machines running Colima and `docker compose` then fails with a baffling flag error.
    """

    def __init__(self, compose_file: Path, spool_port: int):
        self._compose_file = Path(compose_file)
        self._spool_port = spool_port

    def up(self, mail_dir: Path) -> None:
        mail_dir.mkdir(parents=True, exist_ok=True)
        self._compose(mail_dir, "up", "-d")

    def down(self, mail_dir: Path) -> None:
        self._compose(mail_dir, "down")

    def restart(self, mail_dir: Path) -> None:
        self._compose(mail_dir, "restart")

    def logs(self, mail_dir: Path, follow: bool = False) -> int:
        return self._compose(mail_dir, "logs", *(["-f"] if follow else []))

    def wait_until_ready(self, health_url: str, timeout_seconds: int = 30) -> bool:
        for _ in range(timeout_seconds):
            try:
                with urllib.request.urlopen(health_url, timeout=2):
                    return True
            except (urllib.error.URLError, OSError):
                time.sleep(1)
        return False

    def _binary(self) -> list[str]:
        if shutil.which("docker-compose"):
            return ["docker-compose"]
        if shutil.which("docker"):
            return ["docker", "compose"]
        raise SystemExit("neither docker-compose nor docker is on PATH")

    def _compose(self, mail_dir: Path, *args: str) -> int:
        if not self._compose_file.exists():
            raise SystemExit(f"no compose file at {self._compose_file}")
        command = [*self._binary(), "-f", str(self._compose_file), *args]
        completed = subprocess.run(
            command,
            env={
                **os.environ,
                "AIMEL_MAIL_DIR": str(mail_dir),
                "AIMEL_HTTP_PORT": str(self._spool_port),
            },
            check=False,
        )
        return completed.returncode

