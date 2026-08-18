"""
Mini AI Security Lab - Entry Point
Run this file to start the application.
"""

from app.main import app, config

if __name__ == "__main__":
    print(f"\n{'='*50}")
    print(f"  {config['app_name']} v{config['version']}")
    print(f"{'='*50}")
    print(f"  Open: http://{config['host']}:{config['port']}")
    print(f"{'='*50}\n")

    app.run(
        host=config["host"],
        port=config["port"],
        debug=config["debug"]
    )
