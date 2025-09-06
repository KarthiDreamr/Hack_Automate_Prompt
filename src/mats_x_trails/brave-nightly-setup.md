# Brave Nightly Setup Guide

This guide explains how to configure and use Brave Nightly browser with the MATS x Trails automation tool.

## Overview

The automation tool supports both Brave Beta and Brave Nightly browsers. This document covers:
- Installing Brave Nightly
- Configuring the automation for Nightly
- Switching between Beta and Nightly
- Troubleshooting common issues

## Installing Brave Nightly

### Linux (Ubuntu/Debian)

1. **Add Brave's repository** (if not already added):
   ```bash
   sudo curl -fsSLo /usr/share/keyrings/brave-browser-nightly-archive-keyring.gpg https://brave-browser-nightly-apt-release.s3.brave.com/brave-browser-nightly-archive-keyring.gpg
   
   echo "deb [signed-by=/usr/share/keyrings/brave-browser-nightly-archive-keyring.gpg] https://brave-browser-nightly-apt-release.s3.brave.com/ stable main" | sudo tee /etc/apt/sources.list.d/brave-browser-nightly.list
   ```

2. **Update package list and install**:
   ```bash
   sudo apt update
   sudo apt install brave-browser-nightly
   ```

### Linux (Fedora/RHEL)

1. **Add Brave's repository**:
   ```bash
   sudo dnf config-manager --add-repo https://brave-browser-nightly-rpm-release.s3.brave.com/x86_64/
   sudo rpm --import https://brave-browser-nightly-rpm-release.s3.brave.com/brave-core-nightly.asc
   ```

2. **Install Brave Nightly**:
   ```bash
   sudo dnf install brave-browser-nightly
   ```

### macOS

1. **Download from official website**:
   - Visit: https://brave.com/download-nightly/
   - Download the macOS installer
   - Install the application

### Windows

1. **Download from official website**:
   - Visit: https://brave.com/download-nightly/
   - Download the Windows installer
   - Run the installer

## Configuration Options

### Option 1: Multiple Config Files (Recommended)

Create separate configuration files for each browser:

1. **Create Beta config**:
   ```bash
   cp config.yaml config-beta.yaml
   ```

2. **Create Nightly config**:
   ```bash
   cp config.yaml config-nightly.yaml
   ```

3. **Edit `config-nightly.yaml`**:
   ```yaml
   automation_settings:
     browser_executable_path: "brave-browser-nightly"
     user_data_dir: "profiles/brave-nightly"
     remote_debugging_port: 9222
     browser_ws_endpoint: "http://localhost:9222"
   ```

4. **Edit `config-beta.yaml`** (ensure it uses Beta):
   ```yaml
   automation_settings:
     browser_executable_path: "brave-browser-beta"
     user_data_dir: "profiles/brave-beta"
     remote_debugging_port: 9222
     browser_ws_endpoint: "http://localhost:9222"
   ```

### Option 2: Environment Variable Override

You can override the config file using the `HAP_MATS_CONFIG_PATH` environment variable:

```bash
# Use Beta
HAP_MATS_CONFIG_PATH=config-beta.yaml python -m src.mats_x_trails.app

# Use Nightly
HAP_MATS_CONFIG_PATH=config-nightly.yaml python -m src.mats_x_trails.app
```

### Option 3: Shell Aliases

Add these aliases to your `~/.bashrc` or `~/.zshrc`:

```bash
# Brave Beta automation
alias hap-beta="HAP_MATS_CONFIG_PATH=src/mats_x_trails/config-beta.yaml python -m src.mats_x_trails.app"

# Brave Nightly automation
alias hap-nightly="HAP_MATS_CONFIG_PATH=src/mats_x_trails/config-nightly.yaml python -m src.mats_x_trails.app"
```

Then reload your shell:
```bash
source ~/.bashrc  # or ~/.zshrc
```

## Usage Examples

### Using Environment Variables

```bash
# Run with Brave Beta
HAP_MATS_CONFIG_PATH=config-beta.yaml python -m src.mats_x_trails.app --text "My prompt"

# Run with Brave Nightly
HAP_MATS_CONFIG_PATH=config-nightly.yaml python -m src.mats_x_trails.app --text "My prompt"

# Launch new browser instance with Nightly
HAP_MATS_CONFIG_PATH=config-nightly.yaml python -m src.mats_x_trails.app --launch-browser --text "My prompt"
```

### Using Shell Aliases

```bash
# Run with Beta
hap-beta --text "My prompt" --model "fair river"

# Run with Nightly
hap-nightly --text "My prompt" --model "optimistic bird"

# Launch new browser with Nightly
hap-nightly --launch-browser --text "My prompt"
```

## Manual Browser Launch

### Brave Beta
```bash
brave-browser-beta --remote-debugging-port=9222
```

### Brave Nightly
```bash
brave-browser-nightly --remote-debugging-port=9222
```

## Profile Management

Each browser version uses a separate profile directory:
- **Beta**: `profiles/brave-beta/`
- **Nightly**: `profiles/brave-nightly/`

This separation ensures:
- No conflicts between browser versions
- Independent settings and extensions
- Clean testing environment

### Copying Profile Data

If you want to use the same profile data in both browsers:

```bash
# Copy Beta profile to Nightly (optional)
cp -r profiles/brave-beta/* profiles/brave-nightly/
```

**Note**: This is optional and not recommended for testing purposes, as it may cause conflicts.

## Troubleshooting

### Browser Not Found

**Error**: `Could not find 'brave-browser-nightly'`

**Solutions**:
1. Verify installation:
   ```bash
   which brave-browser-nightly
   ```

2. Check if it's in your PATH:
   ```bash
   echo $PATH
   ```

3. Use full path in config:
   ```yaml
   browser_executable_path: "/usr/bin/brave-browser-nightly"
   ```

### Port Already in Use

**Error**: `Port 9222 is already in use`

**Solutions**:
1. Kill existing browser processes:
   ```bash
   pkill -f brave-browser
   ```

2. Use different port in config:
   ```yaml
   remote_debugging_port: 9223
   browser_ws_endpoint: "http://localhost:9223"
   ```

### Profile Directory Issues

**Error**: `Failed to create profile directory`

**Solutions**:
1. Create directory manually:
   ```bash
   mkdir -p profiles/brave-nightly
   ```

2. Check permissions:
   ```bash
   ls -la profiles/
   ```

### Connection Timeout

**Error**: `Failed to connect to browser`

**Solutions**:
1. Ensure browser is running with debugging:
   ```bash
   brave-browser-nightly --remote-debugging-port=9222
   ```

2. Check if debugging endpoint is accessible:
   ```bash
   curl http://localhost:9222/json
   ```

3. Increase browser initialization wait time:
   ```yaml
   browser_init_wait_sec: 10
   ```

## Differences Between Beta and Nightly

| Feature | Beta | Nightly |
|---------|------|---------|
| **Stability** | More stable | Cutting-edge features |
| **Update Frequency** | Weekly | Daily |
| **Bug Risk** | Lower | Higher |
| **New Features** | Delayed | Immediate |
| **Testing** | Production-ready | Experimental |

## Best Practices

1. **Use Beta for production** automation
2. **Use Nightly for testing** new features
3. **Keep separate profiles** for each version
4. **Test thoroughly** before switching versions
5. **Backup configurations** before making changes

## Configuration Reference

### Complete Nightly Config Example

```yaml
base_url: "https://www.hackaprompt.com/track/trails_x_mats/robust_rewording"

automation_settings:
  browser_executable_path: "brave-browser-nightly"
  user_data_dir: "profiles/brave-nightly"
  remote_debugging_port: 9222
  browser_ws_endpoint: "http://localhost:9222"
  navigate_to_base_url: false
  loop_on_failure: true
  browser_init_wait_sec: 5

  timeouts:
    prompt_visible_ms: 1000
    submit_prompt_click_ms: 2000
    submit_for_judging_enable_ms: 180000
    submit_for_judging_click_ms: 180000
    success_visible_ms: 5000
    restart_click_ms: 5000
    continue_button_visible_ms: 5000
    continue_button_click_ms: 5000
    polling_interval_ms: 500
    judging_timeout_sec: 180
    post_refresh_wait_ms: 2000

# ... rest of your configuration
```

## Support

If you encounter issues:
1. Check this troubleshooting section
2. Verify your browser installation
3. Check the main project documentation
4. Review the configuration examples above
