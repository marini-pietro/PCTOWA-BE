import subprocess

processes = []
for server in ["log_server.py", "auth_server.py", "api_server.py"]:
    try:
        process = subprocess.Popen(["python", server])
        processes.append(process)
    except Exception as e:
        print(f"Error occurred while starting {server}: {e}")

# Wait for all processes to complete (optional, if you want to monitor them)
for process in processes:
    process.wait()