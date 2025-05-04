# run_all_workers.py

import subprocess
from config import WORKER_BOTS

for worker_id in WORKER_BOTS.keys():
    print(f"🚀 Starting {worker_id}...")
    subprocess.Popen(['python', 'worker_bot.py', worker_id])


# 🔧 Also launch the raspberry_bot
print("🚀 Starting raspberry_bot...")
subprocess.Popen(['python', 'raspberry_bot.py'])