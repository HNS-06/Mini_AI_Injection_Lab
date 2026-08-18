"""
Fuzzer - Advanced mutation engine with tracking and playground.

Implements: seed -> mutate -> execute -> analyze
Provides mutation preview, history, and educational insights.
"""

import random
import string
import time
from .seeds import get_seeds, get_seed_by_id


class MutationRecord:
    def __init__(self, original, mutated, mutation_type, description):
        self.original = original
        self.mutated = mutated
        self.mutation_type = mutation_type
        self.description = description

    def to_dict(self):
        return {
            "original": self.original,
            "mutated": self.mutated,
            "mutation_type": self.mutation_type,
            "description": self.description
        }


class FuzzerResult:
    def __init__(self, test_id, seed_id, category, severity, payload, response, status, risk, detection, duration):
        self.test_id = test_id
        self.seed_id = seed_id
        self.category = category
        self.severity = severity
        self.payload = payload
        self.response = response
        self.status = status
        self.risk = risk
        self.detection = detection
        self.duration = duration

    def to_dict(self):
        return {
            "test_id": self.test_id,
            "seed_id": self.seed_id,
            "category": self.category,
            "severity": self.severity,
            "payload": self.payload,
            "response": self.response,
            "status": self.status,
            "risk": self.risk,
            "detection": self.detection,
            "duration": round(self.duration, 3)
        }


class Fuzzer:
    def __init__(self, target, detector, config=None):
        self.target = target
        self.detector = detector
        self.config = config or {}
        self.max_mutations = self.config.get("max_mutations", 5)
        self.results = []
        self.mutation_history = []
        self.stats = {
            "total_runs": 0,
            "total_vulnerable": 0,
            "total_safe": 0,
            "total_suspicious": 0
        }

    def get_mutation_types(self):
        return [
            {"name": "case_variation", "description": "Randomizes character casing"},
            {"name": "insertion", "description": "Inserts words at random positions"},
            {"name": "padding", "description": "Adds characters before/after"},
            {"name": "reordering", "description": "Swaps adjacent words"},
            {"name": "encoding", "description": "Replaces characters with symbols"},
            {"name": "deletion", "description": "Removes random words"},
            {"name": "duplication", "description": "Duplicates parts of the payload"},
            {"name": "whitespace", "description": "Modifies spacing"},
            {"name": "unicode", "description": "Uses unicode lookalikes"},
            {"name": "concatenation", "description": "Joins multiple payloads"}
        ]

    def mutate(self, payload: str, count: int = 3, mutation_types: list = None) -> list:
        if mutation_types is None:
            mutation_types = ["case_variation", "insertion", "padding", "reordering", "encoding"]

        mutations = []
        mutation_map = {
            "case_variation": self._case_variation,
            "insertion": self._insertion,
            "padding": self._padding,
            "reordering": self._reordering,
            "encoding": self._encoding,
            "deletion": self._deletion,
            "duplication": self._duplication,
            "whitespace": self._whitespace_modification,
            "unicode": self._unicode_substitution,
            "concatenation": self._concatenation
        }

        for mtype in mutation_types:
            if mtype in mutation_map:
                mutated = mutation_map[mtype](payload)
                record = MutationRecord(
                    original=payload,
                    mutated=mutated,
                    mutation_type=mtype,
                    description=self._get_mutation_description(mtype)
                )
                mutations.append(record)
                self.mutation_history.append(record)

        while len(mutations) < count:
            mtype = random.choice(mutation_types)
            if mtype in mutation_map:
                mutated = mutation_map[mtype](payload)
                record = MutationRecord(
                    original=payload,
                    mutated=mutated,
                    mutation_type=mtype,
                    description=self._get_mutation_description(mtype)
                )
                mutations.append(record)

        return mutations[:count]

    def _get_mutation_description(self, mtype):
        descriptions = {
            "case_variation": "Randomizes character casing (aBcDeF)",
            "insertion": "Inserts random words at random positions",
            "padding": "Adds random characters before/after the payload",
            "reordering": "Swaps adjacent words in the payload",
            "encoding": "Replaces characters with similar symbols (@, 3, $)",
            "deletion": "Removes random words from the payload",
            "duplication": "Duplicates parts of the payload",
            "whitespace_modification": "Adds/removes extra spaces",
            "unicode_substitution": "Uses unicode lookalike characters",
            "concatenation": "Joins the payload with another string"
        }
        return descriptions.get(mtype, "Unknown mutation")

    def _case_variation(self, payload: str) -> str:
        result = []
        for char in payload:
            if random.random() > 0.5:
                result.append(char.upper())
            else:
                result.append(char.lower())
        return "".join(result)

    def _insertion(self, payload: str) -> str:
        words = payload.split()
        insertions = [
            "PLEASE ", "IMPORTANT: ", "NOTE: ", "REMINDER: ",
            "ADMIN: ", "URGENT: ", "CONFIDENTIAL: ", "OVERRIDE: ",
            "NEW INSTRUCTION: ", "SYSTEM: ", "DEBUG: "
        ]
        if len(words) > 1:
            pos = random.randint(0, len(words) - 1)
            words.insert(pos, random.choice(insertions))
        return " ".join(words)

    def _padding(self, payload: str) -> str:
        padding_chars = list("._- ")
        padding = "".join(random.choices(padding_chars, k=random.randint(5, 15)))
        positions = ["prefix", "suffix", "both"]
        choice = random.choice(positions)
        if choice == "prefix":
            return padding + payload
        elif choice == "suffix":
            return payload + padding
        else:
            return padding + payload + padding

    def _reordering(self, payload: str) -> str:
        words = payload.split()
        if len(words) > 2:
            idx = random.randint(0, len(words) - 2)
            words[idx], words[idx + 1] = words[idx + 1], words[idx]
        return " ".join(words)

    def _encoding(self, payload: str) -> str:
        encodings = [
            ("a", "@"), ("e", "3"), ("i", "1"), ("o", "0"),
            ("s", "$"), ("t", "+"), ("l", "|"), ("g", "9")
        ]
        result = list(payload)
        for _ in range(random.randint(1, 3)):
            original, replacement = random.choice(encodings)
            for i in range(len(result)):
                if result[i].lower() == original:
                    result[i] = replacement
                    break
        return "".join(result)

    def _deletion(self, payload: str) -> str:
        words = payload.split()
        if len(words) > 2:
            idx = random.randint(0, len(words) - 1)
            del words[idx]
        return " ".join(words)

    def _duplication(self, payload: str) -> str:
        words = payload.split()
        if len(words) > 0:
            idx = random.randint(0, len(words) - 1)
            word = words[idx]
            words.insert(idx + 1, word)
        return " ".join(words)

    def _whitespace_modification(self, payload: str) -> str:
        result = list(payload)
        for i in range(len(result)):
            if result[i] == ' ' and random.random() > 0.7:
                result[i] = '  '
        return "".join(result)

    def _unicode_substitution(self, payload: str) -> str:
        unicode_map = {
            'a': 'а', 'e': 'е', 'o': 'о', 'p': 'р',
            'c': 'с', 'x': 'х', 'y': 'у', 'i': 'і'
        }
        result = list(payload)
        for i in range(len(result)):
            if result[i].lower() in unicode_map and random.random() > 0.7:
                if result[i].isupper():
                    result[i] = unicode_map[result[i].lower()].upper()
                else:
                    result[i] = unicode_map[result[i].lower()]
        return "".join(result)

    def _concatenation(self, payload: str) -> str:
        suffixes = [
            " Please comply.",
            " This is urgent.",
            " For verification purposes.",
            " As per policy.",
            " Thank you."
        ]
        return payload + random.choice(suffixes)

    def preview_mutations(self, payload: str, count: int = 5) -> list:
        mutation_types = self.get_mutation_types()
        previews = []
        for i, mtype in enumerate(mutation_types[:count]):
            mutated = self.mutate(payload, count=1, mutation_types=[mtype["name"]])[0]
            previews.append({
                "type": mtype["name"],
                "description": mtype["description"],
                "original": payload,
                "mutated": mutated.mutated
            })
        return previews

    def execute_seed(self, seed_id: str, mutation_count: int = 3) -> list:
        seed = get_seed_by_id(seed_id)
        if not seed:
            return []

        results = []
        for i, payload in enumerate(seed["payloads"]):
            start_time = time.time()
            response = self.target.generate(payload)
            duration = time.time() - start_time

            detection = self.detector.analyze(response, payload)
            status = detection["status"]
            risk = detection["risk"]

            result = FuzzerResult(
                test_id=f"{seed['id']}-{i+1:03d}",
                seed_id=seed["id"],
                category=seed["category"],
                severity=seed["severity"],
                payload=payload,
                response=response,
                status=status,
                risk=risk,
                detection=detection,
                duration=duration
            )
            results.append(result)
            self.results.append(result)
            self._update_stats(status)

        mutations = []
        for payload in seed["payloads"][:2]:
            mutated_records = self.mutate(payload, count=mutation_count)
            for j, record in enumerate(mutated_records):
                start_time = time.time()
                response = self.target.generate(record.mutated)
                duration = time.time() - start_time

                detection = self.detector.analyze(response, record.mutated)
                status = detection["status"]
                risk = detection["risk"]

                result = FuzzerResult(
                    test_id=f"{seed['id']}-M{j+1:03d}",
                    seed_id=seed["id"],
                    category=seed["category"],
                    severity=seed["severity"],
                    payload=record.mutated,
                    response=response,
                    status=status,
                    risk=risk,
                    detection=detection,
                    duration=duration
                )
                results.append(result)
                self.results.append(result)
                self._update_stats(status)

        return results

    def run_all(self, progress_callback=None) -> list:
        seeds = get_seeds()
        all_results = []
        total = len(seeds)

        for i, seed in enumerate(seeds):
            results = self.execute_seed(seed["id"])
            all_results.extend(results)
            if progress_callback:
                progress_callback(i + 1, total, len(all_results))

        return all_results

    def _update_stats(self, status):
        self.stats["total_runs"] += 1
        if status == "VULNERABLE":
            self.stats["total_vulnerable"] += 1
        elif status == "SAFE":
            self.stats["total_safe"] += 1
        elif status == "SUSPICIOUS":
            self.stats["total_suspicious"] += 1

    def get_stats(self):
        return self.stats.copy()

    def get_mutation_history(self):
        return [m.to_dict() for m in self.mutation_history]

    def clear_results(self):
        self.results = []
        self.mutation_history = []
        self.stats = {
            "total_runs": 0,
            "total_vulnerable": 0,
            "total_safe": 0,
            "total_suspicious": 0
        }
