from flask import Flask, request, jsonify
import asyncio

app = Flask(__name__)

@app.route('/ces/setup', methods=['POST'])
def setup():
    print("MockApi: Performing setup...")
    asyncio.run(asyncio.sleep(2))  # Simulate setup action
    print("MockApi: Setup complete")
    return jsonify({"status": "setup complete"}), 200


@app.route('/ces/pick', methods=['POST'])
def pick():
    print("MockApi: Picking up tote...")
    asyncio.run(asyncio.sleep(1))  # Simulate pick action
    print("MockApi: Pick complete")
    return jsonify({"status": "pick complete"}), 200


@app.route('/ces/place', methods=['POST'])
def place():
    data = request.json
    drop_off_location = data.get("drop_off_location", "unknown")
    print(f"MockApi: Placing tote at {drop_off_location}...")
    asyncio.run(asyncio.sleep(2))  # Simulate place action
    print(f"MockApi: Placed tote at {drop_off_location}")
    return jsonify({"status": f"placed at {drop_off_location}"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
