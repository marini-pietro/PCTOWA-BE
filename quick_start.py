import subprocess
import signal

processes = []
try:
    for server in ["log_server.py", "auth_server.py", "api_server.py"]:
        processes.append(subprocess.Popen(["python", server]))
    for process in processes:
        process.wait()
except KeyboardInterrupt:
    for process in processes:
        process.send_signal(signal.SIGINT)