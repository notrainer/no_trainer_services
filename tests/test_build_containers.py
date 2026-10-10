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
    def run_script(self, failure="", push=False, tag=""):
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
            env.pop("REGISTRY", None)
            env.pop("TAG", None)
            if tag:
                env["TAG"] = tag
            command = ["bash", str(root / SCRIPT.name)]
            if push:
                command.append("--push")
            result = subprocess.run(command, cwd=root.parent,
                                    env=env, capture_output=True, text=True)
            calls = [json.loads(line) for line in log.read_text().splitlines()]
            return result, calls

    def test_local_build_does_not_publish(self):
        result, calls = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(calls), 6)
        for index, service in enumerate(SERVICES):
            build = calls[index]
            image = f"ghcr.io/notrainer/no_trainer_{service}"
            self.assertEqual(build[0], "build")
            self.assertEqual(build[-1], service)
            self.assertIn("--pull=always", build)
            self.assertIn("--no-cache", build)
            self.assertIn(f"{service}/Containerfile", build)
            self.assertIn("org.opencontainers.image.source=https://github.com/notrainer/no_trainer_services", build)
            self.assertIn("org.opencontainers.image.revision=" + "a" * 40, build)
            self.assertIn(image + ":latest", build)
            self.assertIn(image + ":" + "a" * 40, build)

    def test_publish_latest_revision_and_release_tag(self):
        result, calls = self.run_script(push=True, tag="v1.2.3")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(calls), 24)
        for index, service in enumerate(SERVICES):
            build, revision, release, latest = calls[index * 4:index * 4 + 4]
            image = f"ghcr.io/notrainer/no_trainer_{service}"
            self.assertIn(image + ":v1.2.3", build)
            self.assertEqual(latest, ["push", image + ":latest"])
            self.assertEqual(revision, ["push", image + ":" + "a" * 40])
            self.assertEqual(release, ["push", image + ":v1.2.3"])

    def test_failed_build_stops_before_publishing(self):
        result, calls = self.run_script("build")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual([call[0] for call in calls], ["build"])

    def test_failed_push_stops_before_next_image(self):
        result, calls = self.run_script("push", push=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual([call[0] for call in calls], ["build", "push"])


if __name__ == "__main__":
    unittest.main()
