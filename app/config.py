import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CONFIG_FILE = os.path.join(DATA_DIR, "lab_config.json")

DEFAULT_CONFIG = {
    "app_name": "Mini AI Security Lab",
    "version": "1.0.0",
    "host": "127.0.0.1",
    "port": 5000,
    "debug": True,
    "default_target": "demo_ai",
    "ollama_url": "http://localhost:11434",
    "ollama_model": "llama3.2",
    "scoring": {
        "initial_score": 100,
        "critical_penalty": 25,
        "high_penalty": 15,
        "medium_penalty": 8,
        "low_penalty": 3
    },
    "fuzzer": {
        "max_mutations": 5,
        "tests_per_seed": 3
    }
}


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            user_config = json.load(f)
        config = DEFAULT_CONFIG.copy()
        for key, value in user_config.items():
            if isinstance(value, dict) and key in config:
                config[key].update(value)
            else:
                config[key] = value
        return config
    return DEFAULT_CONFIG.copy()


def save_config(config):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


config = load_config()
