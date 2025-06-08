import subprocess
import time
import signal
import os
import sys
import threading
import requests
from datetime import datetime
from playwright.async_api import Playwright, Browser, Page
from .config_loader import load_config


class BrowserManager:
    """Manages the lifecycle of the automation browser, including process and connection."""

    def __init__(self, playwright: Playwright):
        self.playwright = playwright
        config = load_config() or {}
        automation_settings = config.get("automation_settings", {})
        self.cleanup_config = config.get("cleanup", {})

        self.brave_executable_path = automation_settings.get(
            "browser_executable_path", "brave-browser-beta"
        )
        self.automation_profile_dir = automation_settings.get(
            "user_data_dir", "/tmp/brave-automation"
        )
        self.remote_debugging_port = automation_settings.get(
            "remote_debugging_port", 9222
        )
        self.ws_endpoint = automation_settings.get("browser_ws_endpoint")

        self.browser_process = None
        self.browser: Browser | None = None
        self.page: Page | None = None
        self.monitor_thread = None
        self.monitoring_active = False
        self.last_activity_time = datetime.now()

    async def get_page(self, connect_to_existing: bool = True) -> Page | None:
        """
        Provides a Playwright page object, launching or connecting to a browser as
        needed.
        """
        if connect_to_existing:
            if not self.ws_endpoint:
                print(
                    "Error: browser_ws_endpoint not configured for connecting to "
                    "existing browser."
                )
                return None

            if not self.check_browser_debugging():
                self.start_browser_process()

            print(f"Connecting to existing browser at {self.ws_endpoint}...")
            self.browser = await self.playwright.chromium.connect_over_cdp(
                self.ws_endpoint
            )

            # Find the first non-blank page
            for p in self.browser.contexts[0].pages:
                if p.url != "about:blank":
                    self.page = p
                    break
            if self.page:
                print(f"Connected to existing page with URL: {self.page.url}")
            else:
                print("No suitable existing page found. Creating a new page.")
                self.page = await self.browser.contexts[0].new_page()
        else:
            print("Launching a new browser instance.")
            self.browser = await self.playwright.chromium.launch(headless=False)
            context = await self.browser.new_context()
            self.page = await context.new_page()
            print("Successfully launched new browser and obtained a page.")

        return self.page

    def get_brave_command(self):
        return (
            f"{self.brave_executable_path} "
            f"--remote-debugging-port={self.remote_debugging_port} "
            f"--user-data-dir={self.automation_profile_dir}"
        )

    def start_browser_process(self):
        """Starts the Brave browser with remote debugging."""
        if self.check_browser_debugging():
            print("✅ Detected existing automation browser instance.")
            return

        brave_command = self.get_brave_command()
        print(f"🚀 Starting automation browser: {brave_command}")
        try:
            self.browser_process = subprocess.Popen(
                brave_command.split(),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid if sys.platform != "win32" else None,
            )
            print(f"🌐 Browser started with PID: {self.browser_process.pid}")
            print("⏳ Waiting for browser to initialize...")
            time.sleep(5)  # Give the browser time to start
        except FileNotFoundError:
            print(
                f"❌ Error: Could not find '{self.brave_executable_path}'. "
                "Please ensure it's in your PATH or update config.yaml."
            )
            sys.exit(1)

    def check_browser_activity(self):
        """Check if browser has active tabs or recent activity."""
        try:
            response = requests.get("http://localhost:9222/json", timeout=2)
            if response.status_code == 200:
                tabs = response.json()
                # Consider browser active if it has tabs open
                active_tabs = [
                    tab
                    for tab in tabs
                    if not tab.get("url", "").startswith("chrome://")
                ]
                return len(active_tabs) > 0
        except requests.exceptions.RequestException:
            pass
        return False

    def check_browser_debugging(self):
        """Check if a browser with remote debugging is already running."""
        if not self.ws_endpoint:
            return False
        try:
            # The JSON endpoint is usually at the http equivalent of the ws endpoint
            json_url = self.ws_endpoint.replace("ws://", "http://") + "/json"
            response = requests.get(json_url, timeout=2)
            return response.status_code == 200
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            return False
        except Exception as e:
            print(
                "An unexpected error occurred while checking the browser: {e}"
            )
            return False

    def activity_monitor(self):
        """
        Monitor browser activity and trigger cleanup after inactivity timeout.
        """
        if not self.cleanup_config.get("enabled", False):
            print("🔧 Cleanup monitoring disabled - browser will remain open")
            return

        timeout_config = self.cleanup_config.get(
            "inactivity_timeout", {"hours": 1, "minutes": 30}
        )
        grace_minutes = self.cleanup_config.get("grace_period_minutes", 5)

        timeout_seconds = timeout_config.get("hours", 0) * 3600 + timeout_config.get(
            "minutes", 0
        ) * 60

        print(
            f"⏰ Cleanup enabled: {timeout_config.get('hours', 0)}h "
            f"{timeout_config.get('minutes', 0)}m inactivity timeout"
        )
        print(
            f"⏳ Grace period: {grace_minutes} minutes after automation "
            "completion"
        )

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
                    print(
                        f"🔄 No activity detected for {timeout_config.get('hours', 0)}h "
                        f"{timeout_config.get('minutes', 0)}m"
                    )
                    print("🧹 Initiating automatic cleanup...")
                    self.cleanup_browser()
                    break

            time.sleep(check_interval)

    def start_activity_monitoring(self):
        """Start the activity monitoring in a separate thread."""
        if not self.cleanup_config.get("enabled", False):
            print("📋 Cleanup disabled - you can manage the browser manually")
            return

        self.monitor_thread = threading.Thread(
            target=self.activity_monitor, daemon=True
        )
        self.monitor_thread.start()
        print("🎯 Started inactivity monitoring...")

    def stop_activity_monitoring(self):
        """Stop the activity monitoring."""
        self.monitoring_active = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)

    def cleanup_browser(self):
        """Clean up the browser based on configuration."""
        if not self.browser_process:
            return

        close_mode = self.cleanup_config.get("close_mode", "instance")

        if close_mode == "tabs":
            # Close only automation tabs (implement tab-specific cleanup here)
            print("🗂️ Cleaning up automation tabs...")
            # This would require more sophisticated tab tracking
        else:
            # Close entire browser instance
            print(
                "🔄 Terminating automation browser instance "
                f"(PID: {self.browser_process.pid})..."
            )

            if sys.platform == "win32":
                subprocess.call(
                    ["taskkill", "/F", "/T", "/PID", str(self.browser_process.pid)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                self.browser_process.terminate()
            else:
                try:
                    os.killpg(os.getpgid(self.browser_process.pid), signal.SIGTERM)
                except ProcessLookupError:
                    print(
                        f"Browser process group with PID {self.browser_process.pid} "
                        "already terminated."
                    )
                except Exception as e:
                    print(f"Error during cleanup: {e}")
                    try:
                        os.killpg(os.getpgid(self.browser_process.pid), signal.SIGKILL)
                    except Exception as e_kill:
                        print(f"Force kill error: {e_kill}")

            try:
                self.browser_process.wait(timeout=10)
                print("✅ Browser cleanup completed.")
            except subprocess.TimeoutExpired:
                print("⚠️ Browser cleanup timeout - forcing termination.")
                self.browser_process.kill()
                self.browser_process.wait()
