# 🛡️ Mini AI Injection Lab

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https.mit-license.org)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Flask 3.0+](https://img.shields.io/badge/flask-3.0+-green.svg)](https://flask.palletsprojects.com/)

A lightweight, interactive AI security testing & benchmarking platform designed for hands-on workshops, red teaming simulations, and AI defense engineering. 

Explore, simulate, and defend against AI vulnerabilities including **Prompt Injections**, **DAN Jailbreaks**, **Canary Data Extraction**, **RAG Context Poisoning**, and **LLM Fuzzing**.

---

## ✨ Features

- 💣 **Attack Lab**: Test 30+ pre-built attack seeds across 5 difficulty levels (Beginner to Master) or construct custom prompt payloads.
- 🔍 **Automated Fuzzer**: Run automated mutation tests to discover edge-case prompt injection vectors.
- 🔀 **Mutation Playground**: Experiment with text transformations (Leetspeak, Case Variation, Unicode Homoglyphs, Word Insertion, Padding) to observe how obfuscation evades filters.
- 🛡️ **Security Detector**: Analyze AI model responses against configurable Canary Tokens, Policy Patterns, and custom Regex Detection Rules.
- ⏱️ **Time Challenge Mode**: Race against the clock to discover target vulnerabilities and score points.
- 🏆 **Leaderboard & Reporting**: Track security scores, log historical test results, and export comprehensive JSON security audit reports.
- 🤖 **Flexible Target System**: Built-in **Demo AI** (simulated target with intentional vulnerabilities) and optional **Ollama** integration for local LLM testing (e.g., Llama 3.2).

---

## 🏗️ Architecture Overview

```
          USER / RED TEAMER
                 │
                 ▼
      ┌─────────────────────┐
      │     WEB INTERFACE    │
      └──────────┬──────────┘
                 │
      ┌──────────┴──────────┐
      ▼                     ▼
┌──────────────┐   ┌──────────────────┐
│  ATTACK LAB  │   │  MUTATION ENGINE │
└──────┬───────┘   └────────┬─────────┘
       │                    │
       └─────────┬──────────┘
                 │
                 ▼
      ┌─────────────────────┐
      │    TARGET ENGINE    │
      │  (Demo AI / Ollama) │
      └──────────┬──────────┘
                 │
                 ▼
      ┌─────────────────────┐
      │  SECURITY DETECTOR  │
      │  & SCORING ENGINE   │
      └──────────┬──────────┘
                 │
      ┌──────────┴──────────┐
      ▼                     ▼
┌──────────────┐   ┌──────────────────┐
│ AUDIT REPORT │   │   LEADERBOARD    │
└──────────────┘   └──────────────────┘
```

---

## 🚀 Quick Start

### 🪟 Windows
Simply double-click `run.bat` or run in terminal:
```cmd
run.bat
```

### 🐧 Linux / macOS
Grant execution permissions and launch:
```bash
chmod +x run.sh
./run.sh
```

### 🐍 Manual Setup (Python 3.10+)

```bash
# 1. Clone the repository
git clone https://github.com/HNS-06/Mini_AI_Injection_Lab.git
cd Mini_AI_Injection_Lab

# 2. Create and activate a virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the application
python app.py
```

Open your browser and navigate to:  
👉 **`http://127.0.0.1:5000`**

---

## 🎯 Attack Categories Tested

| Category | Description | Sample Technique |
| :--- | :--- | :--- |
| **Jailbreak** | Bypassing AI safety constraints & alignment | DAN (Do Anything Now), Persona Manipulation, Roleplay |
| **Prompt Injection** | Overriding core system instructions | Delimiter Confusion, Instruction Overrides, Payload Splitting |
| **Data Leakage** | Extracting sensitive or proprietary training data | Canary Token Extraction, Side-Channel Queries |
| **RAG Poisoning** | Injecting untrusted or fake context into knowledge bases | Context Override, Hallucination Triggers, Trust Exploits |
| **LLM Fuzzing** | Boundary testing and structural input corruption | Format String Injection, Token Overflows, Homoglyphs |

---

## 📁 Repository Structure

```
Mini_AI_Injection_Lab/
├── app.py                 # Main entry point launcher
├── requirements.txt       # Dependencies (Flask >= 3.0.0)
├── run.bat                # Automated launcher for Windows
├── run.sh                 # Automated launcher for Linux/macOS
├── app/
│   ├── main.py            # Flask application routes & SSE endpoints
│   ├── config.py          # Lab configuration & settings
│   ├── attacks/
│   │   ├── seeds.py       # Categorized attack payloads & difficulty levels
│   │   └── fuzzer.py      # Mutation engine & fuzzer logic
│   ├── detection/
│   │   ├── detector.py    # Rule-based response analyzer & regex evaluator
│   │   └── scorer.py      # Security score calculator & history tracking
│   ├── target/
│   │   ├── demo_ai.py     # Simulated target AI with intentional vulnerabilities
│   │   └── ollama.py      # Local Ollama LLM integration adapter
│   └── templates/
│       └── index.html     # Interactive Web UI (Single-Page App)
└── data/
    └── lab_config.json    # Initial configuration file
```

---

## 🤝 Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request:
1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git checkout -b feature/AmazingFeature`)
5. Open a Pull Request

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.
