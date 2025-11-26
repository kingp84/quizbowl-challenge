import subprocess
import os
import requests
import time
import sys

# Ensure we run from project root
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Start ngrok (free random domain)
ngrok = subprocess.Popen(["ngrok", "http", "5000"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Wait for ngrok to initialize, then poll its local API
public_url = None
for i in range(15):  # up to ~15 seconds
    try:
        resp = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=1)
        tunnels = resp.json().get("tunnels", [])
        if tunnels:
            # Pick the first https tunnel
            for t in tunnels:
                if t.get("public_url", "").startswith("https://"):
                    public_url = t["public_url"]
                    break
            if public_url:
                break
    except Exception:
        pass
    time.sleep(1)

if public_url:
    print(f"Public URL: {public_url}")
else:
    print("Could not fetch ngrok URL after waiting.")
    # Not fatal — continue to start the app

# Launch the Flask app
# If your main app file has a different name, change "app.py" here.
exit_code = subprocess.call([sys.executable, "app.py"])
sys.exit(exit_code)