from flask import Flask, request, jsonify
import subprocess
import re
import time
from datetime import datetime

app = Flask(__name__)

@app.route("/api", methods=["GET"])
def run_engine():
    url = request.args.get("url")

    if not url:
        return jsonify({
            "success": False,
            "valid": False,
            "error": "url parameter missing"
        }), 400

    start_time = time.time()

    try:
        process = subprocess.run(
            ["python", "engine.py", url],
            capture_output=True,
            text=True,
            timeout=120
        )

        end_time = time.time()
        time_taken = round((end_time - start_time) * 1000, 2)  # ms
        output = process.stdout + process.stderr

        # Speed classification
        if time_taken < 3000:
            speed = "fast"
        elif time_taken < 7000:
            speed = "normal"
        else:
            speed = "slow"

        # Extract KEY
        match = re.search(r"Your KEY:\s*([A-Za-z0-9_-]+)", output)

        if match:
            key = match.group(1)

            return jsonify({
                "success": True,
                "valid": True,
                "engine_status": "success",
                "key": key,
                "expires_in": {
                    "seconds": 600,
                    "human": "10 minutes"
                },
                "time_taken_ms": time_taken,
                "speed": speed,
                "input_url": url,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })

        return jsonify({
            "success": False,
            "valid": False,
            "engine_status": "failed",
            "error": "Key not found",
            "time_taken_ms": time_taken,
            "speed": speed,
            "input_url": url,
            "raw_output": output,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 500

    except subprocess.TimeoutExpired:
        return jsonify({
            "success": False,
            "valid": False,
            "engine_status": "timeout",
            "error": "engine.py timeout",
            "expires_in": {
                "seconds": 600,
                "human": "10 minutes"
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 504

    except Exception as e:
        return jsonify({
            "success": False,
            "valid": False,
            "engine_status": "crashed",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
