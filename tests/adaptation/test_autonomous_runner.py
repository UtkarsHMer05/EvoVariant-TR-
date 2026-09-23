import signal
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.adaptation import run_autonomous


class AutonomousRunnerTest(unittest.TestCase):
    def test_signal_termination_is_distinguished_from_worker_failure(self):
        with patch(
            "scripts.adaptation.run_autonomous.subprocess.run",
            side_effect=subprocess.CalledProcessError(-signal.SIGTERM, ["worker"]),
        ):
            with self.assertRaises(run_autonomous._ChildSignaled) as raised:
                run_autonomous._run(Path("."), "run_caduceus_hpo.py")

        self.assertEqual(raised.exception.script, "run_caduceus_hpo.py")
        self.assertEqual(raised.exception.signal_name, "SIGTERM")
        self.assertEqual(raised.exception.returncode, -signal.SIGTERM)

    def test_non_signal_worker_failure_stays_an_error(self):
        with patch(
            "scripts.adaptation.run_autonomous.subprocess.run",
            side_effect=subprocess.CalledProcessError(2, ["worker"]),
        ):
            with self.assertRaises(subprocess.CalledProcessError):
                run_autonomous._run(Path("."), "run_caduceus_hpo.py")


if __name__ == "__main__":
    unittest.main()
