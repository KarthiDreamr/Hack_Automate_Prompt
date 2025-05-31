import subprocess
import time
import signal
import os
import sys

def main():
    brave_command = "brave-browser --remote-debugging-port=9222"
    main_script_path = os.path.join("src", "main.py") # Ensures OS-agnostic path
    python_executable = sys.executable # Use the same python that's running this script

    brave_process = None
    script_process = None

    # Ensure src is in PYTHONPATH if running main.py as a script
    # This helps with relative imports within the src directory
    env = os.environ.copy()
    project_root = os.path.dirname(os.path.abspath(__file__))
    src_path = os.path.join(project_root, "src")
    if "PYTHONPATH" in env:
        env["PYTHONPATH"] = f"{src_path}{os.pathsep}{env['PYTHONPATH']}"
    else:
        env["PYTHONPATH"] = src_path

    try:
        print(f"Starting Brave browser: {brave_command}")
        # Start Brave in the background.
        # On Linux, preexec_fn=os.setsid is used to create a new session,
        # so we can kill the whole process group later if needed.
        brave_process = subprocess.Popen(brave_command.split(), 
                                         stdout=subprocess.DEVNULL, 
                                         stderr=subprocess.DEVNULL,
                                         preexec_fn=os.setsid if sys.platform != "win32" else None)
        print(f"Brave browser started with PID: {brave_process.pid}. Waiting for it to initialize...")
        time.sleep(5) # Give Brave a few seconds to start

        print(f"Running main automation script: {python_executable} {main_script_path}")
        # Run the main script and wait for it to complete
        script_process = subprocess.Popen([python_executable, main_script_path], env=env)
        script_process.wait() # Wait for main.py to finish

    except FileNotFoundError:
        print(f"Error: Could not find brave-browser. Please ensure it's in your PATH.")
        print("Alternatively, you can provide the full path to the brave-browser executable.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Automation finished or an error occurred. Cleaning up...")
        if script_process and script_process.poll() is None:
            print("Terminating main script...")
            if sys.platform == "win32":
                script_process.terminate()
            else:
                os.killpg(os.getpgid(script_process.pid), signal.SIGTERM)
            script_process.wait(timeout=5) # wait for termination
            if script_process.poll() is None: # if still running
                 if sys.platform == "win32":
                    script_process.kill()
                 else:
                    os.killpg(os.getpgid(script_process.pid), signal.SIGKILL)


        if brave_process:
            print(f"Terminating Brave browser (PID: {brave_process.pid})...")
            if sys.platform == "win32":
                # For Windows, Popen.terminate() might not kill child processes.
                # A more robust way would be taskkill, but let's try terminate first.
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(brave_process.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                brave_process.terminate()

            else:
                # Kill the entire process group started by Brave
                try:
                    os.killpg(os.getpgid(brave_process.pid), signal.SIGTERM)
                except ProcessLookupError:
                    print(f"Brave process group with PID {brave_process.pid} already terminated.")
                except Exception as e:
                    print(f"Error trying to SIGTERM Brave process group: {e}. Attempting SIGKILL.")
                    try:
                        os.killpg(os.getpgid(brave_process.pid), signal.SIGKILL) # Force kill
                    except Exception as e_kill:
                        print(f"Error trying to SIGKILL Brave process group: {e_kill}")

            try:
                brave_process.wait(timeout=10) # Wait for Brave to terminate
                print("Brave browser terminated.")
            except subprocess.TimeoutExpired:
                print("Brave browser did not terminate in time, attempting to force kill.")
                brave_process.kill() # Fallback to kill if terminate + wait fails
                brave_process.wait() # Wait for kill
                print("Brave browser force killed.")
            except Exception as e:
                print(f"Error during Brave cleanup: {e}")
        
        print("Cleanup complete.")

if __name__ == "__main__":
    main() 