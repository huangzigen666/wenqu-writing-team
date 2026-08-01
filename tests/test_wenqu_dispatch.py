from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "wenqu-dispatch"


class DispatchTests(unittest.TestCase):
    def run_dispatch(self, role: str, env_updates: dict[str, str]) -> tuple[subprocess.CompletedProcess[str], Path]:
        workdir = Path(tempfile.mkdtemp(prefix="wenqu-dispatch-test-"))
        env = os.environ.copy()
        env.update(env_updates)
        result = subprocess.run(
            [str(SCRIPT), role, "--task", "连通性测试", "--workdir", str(workdir)],
            text=True, capture_output=True, env=env, check=False,
        )
        return result, workdir

    def test_primary_failure_uses_declared_substitute(self) -> None:
        result, _ = self.run_dispatch("李文章", {
            "WENQU_CMD_CODEX": "/usr/bin/false",
            "WENQU_CMD_CLAUDE": "/usr/bin/printf",
        })
        self.assertEqual(result.returncode, 0)
        self.assertIn("实际执行者=claude", result.stderr)

    def test_all_failures_stop_with_evidence(self) -> None:
        result, workdir = self.run_dispatch("张素材", {
            "WENQU_CMD_AGY": "/usr/bin/false",
            "WENQU_CMD_CLAUDE": "/usr/bin/false",
            "WENQU_CMD_CODEX": "/usr/bin/false",
        })
        self.assertEqual(result.returncode, 1)
        reports = list((workdir / ".wenqu-runs").glob("*-failure.json"))
        self.assertEqual(len(reports), 1)
        report = json.loads(reports[0].read_text(encoding="utf-8"))
        self.assertEqual([item["agent"] for item in report["attempts"]], ["agy", "claude", "codex"])


if __name__ == "__main__":
    unittest.main()
