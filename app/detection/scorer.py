"""
Scorer - Security scoring with leaderboard and history.

Tracks scores, history, and provides leaderboard functionality.
"""

import json
import os
from datetime import datetime


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
LEADERBOARD_FILE = os.path.join(DATA_DIR, "leaderboard.json")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")


class Scorer:
    def __init__(self, config=None):
        config = config or {}
        self.initial_score = config.get("initial_score", 100)
        self.penalties = {
            "critical": config.get("critical_penalty", 25),
            "high": config.get("high_penalty", 15),
            "medium": config.get("medium_penalty", 8),
            "low": config.get("low_penalty", 3)
        }
        self.score = self.initial_score
        self.history = []
        self.findings = []
        self.attack_history = []
        self._load_history()

    def _load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r") as f:
                    data = json.load(f)
                self.attack_history = data.get("attacks", [])
            except Exception:
                self.attack_history = []

    def _save_history(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        data = {"attacks": self.attack_history[-100:]}
        with open(HISTORY_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def reset(self):
        self.score = self.initial_score
        self.history = []
        self.findings = []

    def add_finding(self, finding: dict) -> dict:
        severity = finding.get("severity", "low")
        penalty = self.penalties.get(severity, 0)

        previous_score = self.score
        self.score = max(0, self.score - penalty)

        record = {
            "finding": finding,
            "penalty": penalty,
            "previous_score": previous_score,
            "new_score": self.score
        }
        self.history.append(record)
        self.findings.append(finding)

        return record

    def record_attack(self, payload, response, status, risk, detection, duration):
        record = {
            "timestamp": datetime.now().isoformat(),
            "payload": payload[:200],
            "response": response[:500],
            "status": status,
            "risk": risk,
            "detection_summary": {
                "findings_count": len(detection.get("findings", [])),
                "types": [f.get("type", "unknown") for f in detection.get("findings", [])]
            },
            "duration": round(duration, 3),
            "score_at_time": self.score
        }
        self.attack_history.append(record)
        self._save_history()
        return record

    def calculate_from_results(self, results: list) -> dict:
        self.reset()

        for result in results:
            for finding in result.get("findings", []):
                self.add_finding(finding)

        return self.get_summary()

    def get_summary(self) -> dict:
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for finding in self.findings:
            severity = finding.get("severity", "low")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        return {
            "score": self.score,
            "initial_score": self.initial_score,
            "total_findings": len(self.findings),
            "severity_counts": severity_counts,
            "grade": self._calculate_grade(),
            "history": self.history[-20:]
        }

    def _calculate_grade(self) -> str:
        if self.score >= 90:
            return "A"
        elif self.score >= 80:
            return "B"
        elif self.score >= 70:
            return "C"
        elif self.score >= 60:
            return "D"
        else:
            return "F"

    def get_status_message(self) -> str:
        if self.score >= 90:
            return "Excellent - Strong security posture"
        elif self.score >= 80:
            return "Good - Minor improvements needed"
        elif self.score >= 70:
            return "Fair - Several issues to address"
        elif self.score >= 60:
            return "Poor - Significant vulnerabilities found"
        else:
            return "Critical - Immediate action required"

    def get_attack_history(self, limit=50):
        return self.attack_history[-limit:]

    def clear_history(self):
        self.attack_history = []
        self._save_history()

    def get_leaderboard(self) -> list:
        if os.path.exists(LEADERBOARD_FILE):
            try:
                with open(LEADERBOARD_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_leaderboard(self, leaderboard):
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(LEADERBOARD_FILE, "w") as f:
            json.dump(leaderboard, f, indent=2)

    def add_leaderboard_entry(self, name: str, score: int, tests_completed: int, vulnerabilities_found: int) -> dict:
        entry = {
            "name": name,
            "score": score,
            "tests_completed": tests_completed,
            "vulnerabilities_found": vulnerabilities_found,
            "timestamp": datetime.now().isoformat()
        }

        leaderboard = self.get_leaderboard()
        leaderboard.append(entry)
        leaderboard.sort(key=lambda x: x["score"], reverse=True)
        leaderboard = leaderboard[:20]
        self._save_leaderboard(leaderboard)

        return entry

    def get_leaderboard_rank(self, score: int) -> int:
        leaderboard = self.get_leaderboard()
        for i, entry in enumerate(leaderboard):
            if score >= entry["score"]:
                return i + 1
        return len(leaderboard) + 1
