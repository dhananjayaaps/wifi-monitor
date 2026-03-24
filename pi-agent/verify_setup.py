#!/usr/bin/env python3
"""
WiFi Monitor Pi Agent - Setup Verification Script
Tests system requirements and configuration before deployment.
"""

import sys
import os
import subprocess
import socket
from pathlib import Path

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text.center(60)}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

def print_test(name, passed, details=""):
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"{status} {name}")
    if details:
        print(f"       {details}")

def check_python_version():
    """Check Python version >= 3.7"""
    version = sys.version_info
    passed = version.major == 3 and version.minor >= 7
    details = f"Python {version.major}.{version.minor}.{version.micro}"
    print_test("Python Version", passed, details)
    return passed

def check_os():
    """Check if running on Linux"""
    passed = os.name == 'posix'
    details = f"OS: {os.name}"
    print_test("Operating System", passed, details)
    return passed

def check_command(cmd):
    """Check if a command exists"""
    try:
        subprocess.run([cmd, '--version'], capture_output=True, timeout=2)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

def check_system_tools():
    """Check for required system tools"""
    tools = {
        'sudo': 'Sudo (required for network scanning)',
        'ip': 'iproute2 (network configuration)',
        'iptables': 'iptables (traffic monitoring)',
    }
    
    optional_tools = {
        'arp-scan': 'arp-scan (active network scanning)',
        'nmap': 'nmap (fallback network scanning)',
    }
    
    results = {}
    
    print(f"\n{YELLOW}Required Tools:{RESET}")
    for cmd, desc in tools.items():
        passed = check_command(cmd)
        print_test(desc, passed, f"Command: {cmd}")
        results[cmd] = passed
    
    print(f"\n{YELLOW}Optional Tools (at least one recommended):{RESET}")
    optional_found = False
    for cmd, desc in optional_tools.items():
        passed = check_command(cmd)
        print_test(desc, passed, f"Command: {cmd}")
        if passed:
            optional_found = True
    
    if not optional_found:
        print(f"{YELLOW}⚠ Warning: No scanning tools found. Install arp-scan or nmap for production use.{RESET}")
    
    return all(results.values())

def check_python_packages():
    """Check for required Python packages"""
    packages = ['requests', 'yaml']
    results = {}
    
    print(f"\n{YELLOW}Python Packages:{RESET}")
    for pkg in packages:
        try:
            __import__(pkg)
            print_test(f"{pkg}", True, "Installed")
            results[pkg] = True
        except ImportError:
            print_test(f"{pkg}", False, "Not installed")
            results[pkg] = False
    
    return all(results.values())

def check_network_interfaces():
    """Check available network interfaces"""
    print(f"\n{YELLOW}Network Interfaces:{RESET}")
    try:
        result = subprocess.run(['ip', 'link', 'show'], 
                              capture_output=True, text=True, timeout=5)
        
        interfaces = []
        for line in result.stdout.split('\n'):
            if ': <' in line:
                iface = line.split(':')[1].strip()
                interfaces.append(iface)
        
        if interfaces:
            print_test("Interfaces Found", True, ", ".join(interfaces))
            
            # Check for common interfaces
            has_wlan = any('wlan' in i for i in interfaces)
            has_eth = any('eth' in i for i in interfaces)
            
            if has_wlan:
                print(f"       {GREEN}wlan interface available for WiFi monitoring{RESET}")
            if has_eth:
                print(f"       {GREEN}eth interface available for Ethernet monitoring{RESET}")
            
            return True
        else:
            print_test("Interfaces Found", False, "No interfaces detected")
            return False
            
    except Exception as e:
        print_test("Interface Check", False, str(e))
        return False

def check_proc_net():
    """Check access to /proc/net files"""
    print(f"\n{YELLOW}System Files Access:{RESET}")
    
    files = {
        '/proc/net/arp': 'ARP table (device discovery)',
        '/proc/net/dev': 'Network stats (traffic monitoring)',
    }
    
    results = {}
    for path, desc in files.items():
        exists = Path(path).exists()
        print_test(desc, exists, path)
        results[path] = exists
    
    return all(results.values())

def check_config_file():
    """Check if config.yaml exists and is readable"""
    print(f"\n{YELLOW}Configuration:{RESET}")
    
    config_path = Path('config.yaml')
    if not config_path.exists():
        print_test("config.yaml exists", False, "File not found")
        return False
    
    print_test("config.yaml exists", True, str(config_path.absolute()))
    
    # Try to load config
    try:
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check required fields
        required = ['api_base_url', 'auth', 'interface']
        missing = [field for field in required if field not in config]
        
        if missing:
            print_test("Required fields present", False, f"Missing: {', '.join(missing)}")
            return False
        
        print_test("Required fields present", True, "All required fields found")
        
        # Check auth fields
        if 'email' in config['auth'] and 'password' in config['auth']:
            print_test("Auth configured", True, f"Email: {config['auth']['email']}")
        else:
            print_test("Auth configured", False, "Missing email or password")
            return False
        
        return True
        
    except Exception as e:
        print_test("Config validation", False, str(e))
        return False

def check_permissions():
    """Check file permissions"""
    print(f"\n{YELLOW}Permissions:{RESET}")
    
    # Check if running as root
    is_root = os.geteuid() == 0 if hasattr(os, 'geteuid') else False
    
    if is_root:
        print_test("Running as root", True, "Full system access")
    else:
        print_test("Running as root", False, "Some features require sudo")
        print(f"       {YELLOW}Note: Run tests with sudo for full validation{RESET}")
    
    return True

def test_backend_connectivity(config_path='config.yaml'):
    """Test connection to backend server"""
    print(f"\n{YELLOW}Backend Connectivity:{RESET}")
    
    try:
        import yaml
        import requests
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        api_url = config.get('api_base_url', '')
        if not api_url:
            print_test("Backend URL configured", False, "api_base_url not set")
            return False
        
        print_test("Backend URL configured", True, api_url)
        
        # Extract base URL (remove /api/v1 suffix)
        base_url = api_url.replace('/api/v1', '')
        health_url = f"{base_url}/api/v1/system/health"
        
        try:
            response = requests.get(health_url, timeout=5)
            passed = response.status_code == 200
            details = f"HTTP {response.status_code}"
            print_test("Backend reachable", passed, details)
            return passed
        except requests.exceptions.ConnectionError:
            print_test("Backend reachable", False, "Connection refused")
            return False
        except requests.exceptions.Timeout:
            print_test("Backend reachable", False, "Connection timeout")
            return False
        except Exception as e:
            print_test("Backend reachable", False, str(e))
            return False
            
    except ImportError:
        print_test("Dependencies available", False, "Missing requests or yaml")
        return False
    except Exception as e:
        print_test("Backend test", False, str(e))
        return False

def main():
    """Run all verification tests"""
    print_header("WiFi Monitor Pi Agent - Setup Verification")
    
    print(f"{BLUE}This script verifies your system meets all requirements.{RESET}")
    print(f"{BLUE}Run with 'sudo' for complete testing.{RESET}")
    
    results = {}
    
    # System checks
    print_header("System Requirements")
    results['python'] = check_python_version()
    results['os'] = check_os()
    results['tools'] = check_system_tools()
    
    # Python environment
    print_header("Python Environment")
    results['packages'] = check_python_packages()
    
    # Network
    print_header("Network Configuration")
    results['interfaces'] = check_network_interfaces()
    results['proc'] = check_proc_net()
    
    # Configuration
    print_header("Agent Configuration")
    results['config'] = check_config_file()
    
    # Permissions
    print_header("System Permissions")
    results['permissions'] = check_permissions()
    
    # Backend connectivity
    if results.get('packages') and results.get('config'):
        print_header("Backend Connectivity")
        results['backend'] = test_backend_connectivity()
    
    # Summary
    print_header("Verification Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\nTests passed: {passed}/{total}")
    
    if passed == total:
        print(f"\n{GREEN}✓ All checks passed! System is ready for deployment.{RESET}")
        print(f"\n{BLUE}Next steps:{RESET}")
        print(f"  1. Review configuration: config.yaml")
        print(f"  2. Install as service: sudo bash install.sh")
        print(f"  3. Start service: sudo systemctl start wifi-monitor")
        return 0
    else:
        print(f"\n{RED}✗ Some checks failed. Please address the issues above.{RESET}")
        print(f"\n{YELLOW}Common fixes:{RESET}")
        print(f"  • Install Python packages: pip install -r requirements.txt")
        print(f"  • Install system tools: sudo apt install arp-scan nmap iptables")
        print(f"  • Configure settings: edit config.yaml")
        print(f"  • Check backend: ensure backend server is running")
        return 1

if __name__ == '__main__':
    sys.exit(main())
