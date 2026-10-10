import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "build_containers.sh"
SERVICES = ("dns", "ldap", "mail", "postgres", "samba", "vsftpd")


class PublicationTest(unittest.TestCase):
    def run_script(self, failure=""):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copy2(SCRIPT, root / SCRIPT.name)
            for service in (*SERVICES, "unrelated-directory"):
                (root / service).mkdir()
            binary = root / ".mock-bin"
            binary.mkdir()
            mock = binary / "podman"
            mock.write_text('''#!/usr/bin/env python3
import json, os, sys
with open(os.environ["CALL_LOG"], "a") as log:
    log.write(json.dumps(sys.argv[1:]) + "\\n")
sys.exit(1 if sys.argv[1] == os.environ["FAIL_OPERATION"] else 0)
''')
            mock.chmod(0o755)
            log = root / "calls.jsonl"
            env = os.environ | {
                "PATH": str(binary) + os.pathsep + os.environ["PATH"],
                "CALL_LOG": str(log), "FAIL_OPERATION": failure,
                "GITHUB_REPOSITORY_OWNER": "NoTrainer",
                "GITHUB_REPOSITORY": "notrainer/no_trainer_services",
                "GITHUB_SHA": "a" * 40,
            }
            result = subprocess.run(["bash", str(root / SCRIPT.name)], cwd=root.parent,
                                    env=env, capture_output=True, text=True)
            calls = [json.loads(line) for line in log.read_text().splitlines()]
            return result, calls

    def test_owner_labels_and_only_six_services(self):
        result, calls = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(calls), 18)
        for index, service in enumerate(SERVICES):
            build, latest, revision = calls[index * 3:index * 3 + 3]
            image = f"ghcr.io/notrainer/no_trainer_{service}"
            self.assertEqual(build[0], "build")
            self.assertEqual(build[-1], service)
            self.assertIn(f"{service}/Containerfile", build)
            self.assertIn("org.opencontainers.image.source=https://github.com/notrainer/no_trainer_services", build)
            self.assertIn("org.opencontainers.image.revision=" + "a" * 40, build)
            self.assertEqual(latest, ["push", image + ":latest"])
            self.assertEqual(revision, ["push", image + ":" + "a" * 40])

    def test_failed_build_stops_before_publishing(self):
        result, calls = self.run_script("build")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual([call[0] for call in calls], ["build"])

    def test_failed_push_stops_before_next_image(self):
        result, calls = self.run_script("push")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual([call[0] for call in calls], ["build", "push"])


if __name__ == "__main__":
    unittest.main()
