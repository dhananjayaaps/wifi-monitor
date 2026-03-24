"""Entry point for Pi Agent."""
import sys
import argparse
from pathlib import Path
from .agent import Agent
from .config import Config


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="WiFi Monitor Pi Agent - Network monitoring agent for Raspberry Pi"
    )
    parser.add_argument(
        "-c", "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)"
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version="WiFi Monitor Pi Agent v1.0.0"
    )
    parser.add_argument(
        "--test-config",
        action="store_true",
        help="Test configuration and exit"
    )
    return parser.parse_args()


def test_config(config_path: str):
    """Test configuration file and report any issues."""
    print(f"Testing configuration: {config_path}")
    
    if not Path(config_path).exists():
        print(f"❌ Configuration file not found: {config_path}")
        return False
    
    try:
        config = Config(config_path)
        print("\n✓ Configuration loaded successfully")
        print(f"\nConfiguration Summary:")
        print(f"  Backend URL: {config.api_base_url}")
        print(f"  Interface: {config.interface}")
        print(f"  Simulation mode: {config.simulation_mode}")
        print(f"  Scan interval: {config.scan_interval}s")
        print(f"  Stats interval: {config.stats_interval}s")
        print(f"  Log level: {config.log_level}")
        print(f"  Log directory: {config.log_dir}")
        
        if not config.auth_email or not config.auth_password:
            print(f"\n⚠️  Warning: Authentication credentials not set")
            print(f"  Please configure auth.email and auth.password")
            return False
        else:
            print(f"  Auth email: {config.auth_email}")
        
        print("\n✓ Configuration is valid")
        return True
        
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return False


def main():
    """Main entry point."""
    args = parse_args()
    
    # Test config if requested
    if args.test_config:
        success = test_config(args.config)
        sys.exit(0 if success else 1)
    
    # Create and start agent
    try:
        agent = Agent(config_path=args.config)
        agent.start()
    except KeyboardInterrupt:
        print("\n\nAgent stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
