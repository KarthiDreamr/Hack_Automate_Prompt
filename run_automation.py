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
    main_script_path = os.path.join("src", "main.py")
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

        print(f"⚡ Running automation: {python_executable} {main_script_path}")
        manager.script_process = subprocess.Popen([python_executable, main_script_path], env=env)
        manager.script_process.wait()
        
        print("✅ Automation completed!")
        
        # Start monitoring for delayed cleanup
        manager.start_activity_monitoring()
        
        # Keep the main thread alive if monitoring is enabled
        if manager.cleanup_config.get('enabled', False):
            print("🔍 Monitoring browser activity... (Ctrl+C to stop)")
            try:
                while manager.monitoring_active and manager.monitor_thread.is_alive():
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Manual termination requested")
                manager.stop_activity_monitoring()
                # Only cleanup on manual interrupt if never_auto_close is disabled
                if not manager.cleanup_config.get('never_auto_close', True):
                    manager.cleanup_browser()
                else:
                    print("🚫 Auto-close disabled - browser left running")
        else:
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
            print("⚠️ Terminating running script...")
            if sys.platform == "win32":
                manager.script_process.terminate()
            else:
                os.killpg(os.getpgid(manager.script_process.pid), signal.SIGTERM)
            manager.script_process.wait(timeout=5)
        
        manager.stop_activity_monitoring()
        
        # Check if we should never auto-close the browser
        never_auto_close = manager.cleanup_config.get('never_auto_close', True)
        
        if never_auto_close:
            print("🚫 Auto-close disabled - browser left running permanently")
        else:
            # Only cleanup browser if monitoring was never enabled (immediate cleanup mode)
            if not manager.cleanup_config.get('enabled', False) and manager.brave_process:
                manager.cleanup_browser()
        
        print("✨ Cleanup complete.")

if __name__ == "__main__":
    main() 