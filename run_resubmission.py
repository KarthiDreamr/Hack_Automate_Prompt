import subprocess
import time
import signal
import os
import sys
from src.browser_process_manager import BrowserManager

def main():
    manager = BrowserManager()
    
    automation_profile_dir = "/tmp/brave-automation"
    brave_command = f"brave-browser-beta --remote-debugging-port=9222 --user-data-dir={automation_profile_dir}"
    resubmit_script_path = os.path.join("src", "resubmit_main.py")
    python_executable = sys.executable

    # Set up environment
    env = os.environ.copy()
    project_root = os.path.dirname(os.path.abspath(__file__))
    src_path = os.path.join(project_root, "src")
    if "PYTHONPATH" in env:
        env["PYTHONPATH"] = f"{src_path}{os.pathsep}{env['PYTHONPATH']}"
    else:
        env["PYTHONPATH"] = src_path

    try:
        if manager.check_browser_debugging():
            print("✅ Detected existing automation browser instance.")
        else:
            print(f"🚀 Starting automation browser: {brave_command}")
            manager.brave_process = subprocess.Popen(brave_command.split(), 
                                                   stdout=subprocess.DEVNULL, 
                                                   stderr=subprocess.DEVNULL,
                                                   preexec_fn=os.setsid if sys.platform != "win32" else None)
            print(f"🌐 Browser started with PID: {manager.brave_process.pid}")
            print("⏳ Waiting for browser to initialize...")
            time.sleep(5)

        print(f"⚡ Running resubmission script: {python_executable} {resubmit_script_path}")
        manager.script_process = subprocess.Popen([python_executable, resubmit_script_path], env=env)
        manager.script_process.wait()
        
        print("✅ Resubmission script completed!")
        
        # We don't need the complex monitoring and cleanup for the resubmit script,
        # as it's designed to be run and monitored manually.
        # The user can stop it with Ctrl+C.
        print("📌 Browser left running - manage it manually when ready")

    except FileNotFoundError:
        print(f"❌ Error: Could not find brave-browser-beta. Please ensure it's in your PATH.")
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ An error occurred: {e}")
    finally:
        print("🧹 Final cleanup...")
        if manager.script_process and manager.script_process.poll() is None:
            print("⚠️ Terminating running resubmission script...")
            if sys.platform == "win32":
                manager.script_process.terminate()
            else:
                # Use killpg to terminate the entire process group
                try:
                    os.killpg(os.getpgid(manager.script_process.pid), signal.SIGTERM)
                except ProcessLookupError:
                    pass # Process might have already terminated
            manager.script_process.wait(timeout=5)
        
        # The resubmission script is often long-running, so we default to never closing the browser.
        print("🚫 Auto-close disabled - browser left running.")
        print("✨ Cleanup complete.")

if __name__ == "__main__":
    main() 