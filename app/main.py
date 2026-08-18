"""
Mini AI Security Lab - Main Application

Professional AI security testing platform with real-time features.
"""

import os
import sys
import json
import threading
import time
import queue
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, Response

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from target.demo_ai import DemoAI
from target.ollama import OllamaAI
from attacks.seeds import (
    get_seeds, get_seed_by_id, get_categories, get_levels,
    get_seeds_by_level, add_custom_seed, calculate_unlock_status
)
from attacks.fuzzer import Fuzzer
from detection.detector import Detector
from detection.scorer import Scorer

app = Flask(__name__)
app.config["SECRET_KEY"] = "mini-ai-security-lab-2026"

demo_ai = DemoAI()
ollama_ai = None
current_target = demo_ai
detector = Detector()
scorer = Scorer(config.get("scoring", {}))

fuzzer = Fuzzer(target=current_target, detector=detector, config=config.get("fuzzer", {}))

fuzzer_status = {
    "running": False,
    "progress": 0,
    "total": 0,
    "completed": 0,
    "results": [],
    "current_seed": ""
}

session_data = {
    "tests_completed": 0,
    "vulnerabilities_found": 0,
    "unlocked_levels": {1: True, 2: False, 3: False, 4: False, 5: False},
    "challenge_timer": None,
    "challenge_start": None,
    "challenge_active": False
}

event_queues = []
event_lock = threading.Lock()


def emit_event(event_type, data):
    event = json.dumps({"type": event_type, "data": data, "timestamp": time.time()})
    with event_lock:
        dead_queues = []
        for q in event_queues:
            try:
                q.put_nowait(event)
            except queue.Full:
                dead_queues.append(q)
        for q in dead_queues:
            event_queues.remove(q)


def check_ollama():
    global ollama_ai
    try:
        ollama = OllamaAI(
            url=config.get("ollama_url", "http://localhost:11434"),
            model=config.get("ollama_model", "llama3.2")
        )
        if ollama.online:
            ollama_ai = ollama
            return True
    except Exception:
        pass
    return False


@app.route("/")
def index():
    ollama_available = check_ollama()
    return render_template("index.html",
                         app_name=config["app_name"],
                         version=config["version"],
                         target_name=current_target.name,
                         target_online=current_target.online,
                         ollama_available=ollama_available)


@app.route("/api/events")
def api_events():
    q = queue.Queue(maxsize=100)
    with event_lock:
        event_queues.append(q)

    def generate():
        yield f"data: {json.dumps({'type': 'connected', 'data': {'message': 'Connected to event stream'}})}\n\n"
        try:
            while True:
                try:
                    event = q.get(timeout=30)
                    yield f"data: {event}\n\n"
                except queue.Empty:
                    yield f"data: {json.dumps({'type': 'heartbeat', 'data': {}})}\n\n"
        except GeneratorExit:
            with event_lock:
                if q in event_queues:
                    event_queues.remove(q)

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/api/status")
def api_status():
    ollama_available = check_ollama()
    return jsonify({
        "app_name": config["app_name"],
        "version": config["version"],
        "target": current_target.get_info(),
        "ollama_available": ollama_available,
        "fuzzer_running": fuzzer_status["running"],
        "score": scorer.get_summary(),
        "session": {
            "tests_completed": session_data["tests_completed"],
            "vulnerabilities_found": session_data["vulnerabilities_found"],
            "unlocked_levels": session_data["unlocked_levels"]
        }
    })


@app.route("/api/target", methods=["POST"])
def api_set_target():
    global current_target, fuzzer
    data = request.get_json()
    target_type = data.get("target", "demo_ai")

    if target_type == "ollama" and ollama_ai:
        current_target = ollama_ai
    else:
        current_target = demo_ai

    fuzzer = Fuzzer(target=current_target, detector=detector, config=config.get("fuzzer", {}))
    emit_event("target_changed", {"target": current_target.get_info()})

    return jsonify({
        "target": current_target.get_info(),
        "message": f"Target switched to {current_target.name}"
    })


@app.route("/api/test", methods=["POST"])
def api_run_test():
    data = request.get_json()
    test_type = data.get("test_type", "custom")
    payload = data.get("payload", "")
    context = data.get("context", None)

    emit_event("test_started", {"payload": payload[:100]})

    start_time = time.time()
    response = current_target.generate(payload, context)
    duration = time.time() - start_time

    detection = detector.analyze(response, payload)

    for finding in detection.get("findings", []):
        scorer.add_finding(finding)

    session_data["tests_completed"] += 1
    if detection["status"] == "VULNERABLE":
        session_data["vulnerabilities_found"] += 1

    scorer.record_attack(payload, response, detection["status"], detection["risk"], detection, duration)
    _update_unlocks()

    result = {
        "payload": payload,
        "response": response,
        "detection": detection,
        "duration": round(duration, 3),
        "score": scorer.get_summary()
    }

    emit_event("test_completed", {
        "status": detection["status"],
        "risk": detection["risk"],
        "payload": payload[:100],
        "score": scorer.score,
        "session": {
            "tests_completed": session_data["tests_completed"],
            "vulnerabilities_found": session_data["vulnerabilities_found"]
        }
    })

    return jsonify(result)


@app.route("/api/seeds")
def api_get_seeds():
    seeds = get_seeds()
    return jsonify({
        "seeds": seeds,
        "categories": get_categories(),
        "levels": get_levels()
    })


@app.route("/api/seeds/level/<int:level>")
def api_get_seeds_by_level(level):
    seeds = get_seeds_by_level(level)
    return jsonify({"seeds": seeds, "level": level})


@app.route("/api/seeds/custom", methods=["POST"])
def api_add_custom_seed():
    data = request.get_json()
    success = add_custom_seed(data)
    if success:
        emit_event("seed_added", {"seed_id": data.get("id")})
        return jsonify({"message": "Custom seed added", "seed": data})
    return jsonify({"error": "Invalid seed data"}), 400


@app.route("/api/mutations/preview", methods=["POST"])
def api_mutation_preview():
    data = request.get_json()
    payload = data.get("payload", "")
    count = data.get("count", 5)
    previews = fuzzer.preview_mutations(payload, count)
    return jsonify({"previews": previews})


@app.route("/api/mutations/types")
def api_mutation_types():
    return jsonify({"types": fuzzer.get_mutation_types()})


@app.route("/api/mutations/history")
def api_mutation_history():
    return jsonify({"history": fuzzer.get_mutation_history()})


@app.route("/api/fuzzer/start", methods=["POST"])
def api_fuzzer_start():
    if fuzzer_status["running"]:
        return jsonify({"error": "Fuzzer already running"}), 400

    data = request.get_json() or {}
    seed_id = data.get("seed_id")

    def run_fuzzer():
        global fuzzer_status
        fuzzer_status["running"] = True
        fuzzer_status["results"] = []
        fuzzer_status["progress"] = 0

        emit_event("fuzzer_started", {"seed_id": seed_id})

        try:
            if seed_id:
                results = fuzzer.execute_seed(seed_id)
                fuzzer_status["results"] = [r.to_dict() for r in results]
            else:
                def progress_callback(completed, total, count):
                    fuzzer_status["total"] = total
                    fuzzer_status["completed"] = completed
                    fuzzer_status["progress"] = int((completed / total) * 100) if total > 0 else 0
                    emit_event("fuzzer_progress", {
                        "progress": fuzzer_status["progress"],
                        "completed": completed,
                        "total": total,
                        "count": count
                    })

                results = fuzzer.run_all(progress_callback)
                fuzzer_status["results"] = [r.to_dict() for r in results]
                fuzzer_status["progress"] = 100

            for result in fuzzer_status["results"]:
                for finding in result.get("detection", {}).get("findings", []):
                    scorer.add_finding(finding)
                session_data["tests_completed"] += 1
                if result.get("status") == "VULNERABLE":
                    session_data["vulnerabilities_found"] += 1

            _update_unlocks()

            emit_event("fuzzer_completed", {
                "results_count": len(fuzzer_status["results"]),
                "stats": fuzzer.get_stats(),
                "score": scorer.get_summary()
            })

        except Exception as e:
            fuzzer_status["error"] = str(e)
            emit_event("fuzzer_error", {"error": str(e)})
        finally:
            fuzzer_status["running"] = False

    thread = threading.Thread(target=run_fuzzer)
    thread.daemon = True
    thread.start()

    return jsonify({"message": "Fuzzer started", "seed_id": seed_id})


@app.route("/api/fuzzer/status")
def api_fuzzer_status():
    return jsonify(fuzzer_status)


@app.route("/api/fuzzer/stop", methods=["POST"])
def api_fuzzer_stop():
    fuzzer_status["running"] = False
    emit_event("fuzzer_stopped", {})
    return jsonify({"message": "Fuzzer stopped"})


@app.route("/api/fuzzer/stats")
def api_fuzzer_stats():
    return jsonify(fuzzer.get_stats())


@app.route("/api/results")
def api_get_results():
    return jsonify({
        "results": scorer.get_attack_history(50),
        "score": scorer.get_summary()
    })


@app.route("/api/results/clear", methods=["POST"])
def api_clear_results():
    scorer.reset()
    scorer.clear_history()
    fuzzer.clear_results()
    session_data["tests_completed"] = 0
    session_data["vulnerabilities_found"] = 0
    session_data["unlocked_levels"] = {1: True, 2: False, 3: False, 4: False, 5: False}
    emit_event("results_cleared", {})
    return jsonify({"message": "Results cleared", "score": scorer.get_summary()})


@app.route("/api/score")
def api_get_score():
    return jsonify(scorer.get_summary())


@app.route("/api/history")
def api_get_history():
    limit = request.args.get("limit", 50, type=int)
    return jsonify({"history": scorer.get_attack_history(limit)})


@app.route("/api/history/clear", methods=["POST"])
def api_clear_history():
    scorer.clear_history()
    return jsonify({"message": "History cleared"})


@app.route("/api/leaderboard")
def api_get_leaderboard():
    return jsonify({"leaderboard": scorer.get_leaderboard()})


@app.route("/api/leaderboard/add", methods=["POST"])
def api_add_leaderboard():
    data = request.get_json()
    name = data.get("name", "Anonymous")
    entry = scorer.add_leaderboard_entry(
        name=name,
        score=scorer.score,
        tests_completed=session_data["tests_completed"],
        vulnerabilities_found=session_data["vulnerabilities_found"]
    )
    emit_event("leaderboard_updated", {"entry": entry, "rank": scorer.get_leaderboard_rank(scorer.score)})
    return jsonify({"entry": entry, "rank": scorer.get_leaderboard_rank(scorer.score)})


@app.route("/api/detector/rules")
def api_get_detector_rules():
    return jsonify(detector.get_rules())


@app.route("/api/detector/test", methods=["POST"])
def api_test_detector():
    data = request.get_json()
    response_text = data.get("response", "")
    result = detector.analyze(response_text)
    return jsonify(result)


@app.route("/api/detector/rules/canary", methods=["POST"])
def api_update_canary_tokens():
    data = request.get_json()
    tokens = data.get("tokens", [])
    detector.update_canary_tokens(tokens)
    emit_event("rules_updated", {"type": "canary"})
    return jsonify({"message": "Canary tokens updated", "tokens": tokens})


@app.route("/api/detector/rules/policy", methods=["POST"])
def api_update_policy_patterns():
    data = request.get_json()
    patterns = data.get("patterns", [])
    detector.update_policy_patterns(patterns)
    emit_event("rules_updated", {"type": "policy"})
    return jsonify({"message": "Policy patterns updated", "patterns": patterns})


@app.route("/api/detector/rules/suspicious", methods=["POST"])
def api_update_suspicious_patterns():
    data = request.get_json()
    patterns = data.get("patterns", [])
    detector.update_suspicious_patterns(patterns)
    emit_event("rules_updated", {"type": "suspicious"})
    return jsonify({"message": "Suspicious patterns updated", "patterns": patterns})


@app.route("/api/detector/rules/custom", methods=["POST"])
def api_add_custom_rule():
    data = request.get_json()
    success = detector.add_custom_rule(data)
    if success:
        emit_event("rules_updated", {"type": "custom"})
        return jsonify({"message": "Custom rule added", "rule": data})
    return jsonify({"error": "Invalid rule data"}), 400


@app.route("/api/detector/rules/custom/<int:index>/toggle", methods=["POST"])
def api_toggle_custom_rule(index):
    success = detector.toggle_custom_rule(index)
    if success:
        emit_event("rules_updated", {"type": "custom"})
        return jsonify({"message": "Rule toggled"})
    return jsonify({"error": "Rule not found"}), 404


@app.route("/api/detector/rules/custom/<int:index>/delete", methods=["POST"])
def api_delete_custom_rule(index):
    success = detector.remove_custom_rule(index)
    if success:
        emit_event("rules_updated", {"type": "custom"})
        return jsonify({"message": "Rule deleted"})
    return jsonify({"error": "Rule not found"}), 404


@app.route("/api/detector/rules/reset", methods=["POST"])
def api_reset_detector_rules():
    detector.reset_to_defaults()
    emit_event("rules_updated", {"type": "reset"})
    return jsonify({"message": "Rules reset to defaults"})


@app.route("/api/session")
def api_get_session():
    _update_unlocks()
    return jsonify({
        "tests_completed": session_data["tests_completed"],
        "vulnerabilities_found": session_data["vulnerabilities_found"],
        "unlocked_levels": session_data["unlocked_levels"]
    })


@app.route("/api/session/reset", methods=["POST"])
def api_reset_session():
    session_data["tests_completed"] = 0
    session_data["vulnerabilities_found"] = 0
    session_data["unlocked_levels"] = {1: True, 2: False, 3: False, 4: False, 5: False}
    scorer.reset()
    emit_event("session_reset", {})
    return jsonify({"message": "Session reset"})


@app.route("/api/challenge/start", methods=["POST"])
def api_start_challenge():
    data = request.get_json() or {}
    challenge_type = data.get("type", "time")
    duration = data.get("duration", 300)

    session_data["challenge_active"] = True
    session_data["challenge_start"] = time.time()
    session_data["challenge_duration"] = duration
    session_data["challenge_type"] = challenge_type
    session_data["challenge_findings"] = []

    emit_event("challenge_started", {"type": challenge_type, "duration": duration})

    return jsonify({
        "message": "Challenge started",
        "type": challenge_type,
        "duration": duration
    })


@app.route("/api/challenge/status")
def api_challenge_status():
    if not session_data["challenge_active"]:
        return jsonify({"active": False})

    elapsed = time.time() - session_data["challenge_start"]
    remaining = max(0, session_data.get("challenge_duration", 300) - elapsed)

    if remaining <= 0:
        session_data["challenge_active"] = False
        emit_event("challenge_completed", {"elapsed": elapsed})

    return jsonify({
        "active": session_data["challenge_active"],
        "type": session_data.get("challenge_type", "time"),
        "elapsed": round(elapsed, 1),
        "remaining": round(remaining, 1),
        "findings": session_data.get("challenge_findings", [])
    })


@app.route("/api/challenge/stop", methods=["POST"])
def api_stop_challenge():
    session_data["challenge_active"] = False
    emit_event("challenge_stopped", {})
    return jsonify({"message": "Challenge stopped"})


@app.route("/api/export")
def api_export_report():
    report = {
        "report_title": "AI Security Lab Report",
        "generated_at": datetime.now().isoformat(),
        "target": current_target.get_info(),
        "session": {
            "tests_completed": session_data["tests_completed"],
            "vulnerabilities_found": session_data["vulnerabilities_found"]
        },
        "score": scorer.get_summary(),
        "findings": scorer.findings,
        "attack_history": scorer.get_attack_history(100),
        "detector_rules": detector.get_rules(),
        "fuzzer_stats": fuzzer.get_stats()
    }

    os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data"), exist_ok=True)
    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "security_report.json")

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    return jsonify(report)


@app.route("/api/export/download")
def api_download_report():
    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "security_report.json")
    if os.path.exists(report_path):
        return send_file(report_path, as_attachment=True, download_name="security_report.json")
    return jsonify({"error": "No report available. Run export first."}), 404


@app.route("/api/hints/<seed_id>")
def api_get_hints(seed_id):
    seed = get_seed_by_id(seed_id)
    if seed:
        return jsonify({"hints": seed.get("hints", []), "seed_id": seed_id})
    return jsonify({"hints": [], "seed_id": seed_id})


def _update_unlocks():
    completed = session_data["tests_completed"]
    session_data["unlocked_levels"] = calculate_unlock_status(completed)


def create_app():
    return app


if __name__ == "__main__":
    print(f"\n{'='*60}")
    print(f"  {config['app_name']} v{config['version']}")
    print(f"{'='*60}")
    print(f"  Target: {current_target.name}")
    check_ollama()
    if ollama_ai:
        print(f"  Ollama: Available ({config.get('ollama_model', 'llama3.2')})")
    else:
        print(f"  Ollama: Not available (using Demo AI)")
    print(f"{'='*60}")
    print(f"  Open: http://{config['host']}:{config['port']}")
    print(f"{'='*60}\n")

    app.run(
        host=config["host"],
        port=config["port"],
        debug=config["debug"]
    )
