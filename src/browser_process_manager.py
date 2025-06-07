import subprocess
import time
import signal
import os
import sys
import threading
import requests
import yaml
from datetime import datetime, timedelta

class BrowserManager:
    def __init__(self, config_path="config.yaml"):
        self.brave_process = None
        self.script_process = None
        self.cleanup_config = self.load_cleanup_config(config_path)
        self.last_activity_time = datetime.now()
        self.monitoring_active = False
        self.monitor_thread = None
        
    def load_cleanup_config(self, config_path):
        """Load cleanup configuration from YAML file."""
        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
                return config.get('cleanup', {
                    'enabled': False,
                    'never_auto_close': True,
                    'inactivity_timeout': {'hours': 1, 'minutes': 30},
                    'close_mode': 'instance',
                    'grace_period_minutes': 5
                })
        except Exception as e:
            print(f"Warning: Could not load cleanup config: {e}")
            return {'enabled': False, 'never_auto_close': True}
    
    def check_browser_activity(self):
        """Check if browser has active tabs or recent activity."""
        try:
            response = requests.get("http://localhost:9222/json", timeout=2)
            if response.status_code == 200:
                tabs = response.json()
                # Consider browser active if it has tabs open
                active_tabs = [tab for tab in tabs if not tab.get('url', '').startswith('chrome://')]
                return len(active_tabs) > 0
        except:
            pass
        return False
    
    def check_browser_debugging(self):
        """Check if a browser with remote debugging is already running."""
        try:
            response = requests.get("http://localhost:9222/json", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def activity_monitor(self):
        """Monitor browser activity and trigger cleanup after inactivity timeout."""
        if not self.cleanup_config.get('enabled', False):
            print("🔧 Cleanup monitoring disabled - browser will remain open")
            return
            
        timeout_config = self.cleanup_config.get('inactivity_timeout', {'hours': 1, 'minutes': 30})
        grace_minutes = self.cleanup_config.get('grace_period_minutes', 5)
        
        timeout_seconds = (timeout_config.get('hours', 0) * 3600 + 
                          timeout_config.get('minutes', 0) * 60)
        
        print(f"⏰ Cleanup enabled: {timeout_config.get('hours', 0)}h {timeout_config.get('minutes', 0)}m inactivity timeout")
        print(f"⏳ Grace period: {grace_minutes} minutes after automation completion")
        
        # Grace period after automation completion
        time.sleep(grace_minutes * 60)
        
        self.monitoring_active = True
        check_interval = 30  # Check every 30 seconds
        
        while self.monitoring_active:
            if self.check_browser_activity():
                self.last_activity_time = datetime.now()
            else:
                time_since_activity = datetime.now() - self.last_activity_time
                if time_since_activity.total_seconds() >= timeout_seconds:
                    print(f"🔄 No activity detected for {timeout_config.get('hours', 0)}h {timeout_config.get('minutes', 0)}m")
                    print("🧹 Initiating automatic cleanup...")
                    self.cleanup_browser()
                    break
            
            time.sleep(check_interval)
    
    def start_activity_monitoring(self):
        """Start the activity monitoring in a separate thread."""
        if not self.cleanup_config.get('enabled', False):
            print("📋 Cleanup disabled - you can manage the browser manually")
            return
            
        self.monitor_thread = threading.Thread(target=self.activity_monitor, daemon=True)
        self.monitor_thread.start()
        print("🎯 Started inactivity monitoring...")
    
    def stop_activity_monitoring(self):
        """Stop the activity monitoring."""
        self.monitoring_active = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
    
    def cleanup_browser(self):
        """Clean up the browser based on configuration."""
        if not self.brave_process:
            return
            
        close_mode = self.cleanup_config.get('close_mode', 'instance')
        
        if close_mode == 'tabs':
            # Close only automation tabs (implement tab-specific cleanup here)
            print("🗂️ Cleaning up automation tabs...")
            # This would require more sophisticated tab tracking
        else:
            # Close entire browser instance
            print(f"🔄 Terminating automation browser instance (PID: {self.brave_process.pid})...")
            
            if sys.platform == "win32":
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(self.brave_process.pid)], 
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.brave_process.terminate()
            else:
                try:
                    os.killpg(os.getpgid(self.brave_process.pid), signal.SIGTERM)
                except ProcessLookupError:
                    print(f"Browser process group with PID {self.brave_process.pid} already terminated.")
                except Exception as e:
                    print(f"Error during cleanup: {e}")
                    try:
                        os.killpg(os.getpgid(self.brave_process.pid), signal.SIGKILL)
                    except Exception as e_kill:
                        print(f"Force kill error: {e_kill}")
            
            try:
                self.brave_process.wait(timeout=10)
                print("✅ Browser cleanup completed.")
            except subprocess.TimeoutExpired:
                print("⚠️ Browser cleanup timeout - forcing termination.")
                self.brave_process.kill()
                self.brave_process.wait() 