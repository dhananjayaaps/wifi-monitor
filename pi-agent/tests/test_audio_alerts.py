#!/usr/bin/env python3
"""Test the audio alert system.

This script verifies that:
1. The audio hardware is working
2. The TTS engine is properly configured
3. Voice alerts can be played successfully

Run this on your Raspberry Pi before enabling audio alerts in production.
"""

import argparse
import sys
import time
from pathlib import Path

# Add parent directory to path so we can import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.audio_alert import AudioAlertSystem
except ImportError as e:
    print(f"Error importing AudioAlertSystem: {e}")
    print("Make sure you're running this from the pi-agent directory")
    sys.exit(1)


def test_audio_system(engine="auto", volume=80, language="en"):
    """Test the audio alert system with various scenarios."""
    
    print("=" * 60)
    print("Audio Alert System Test")
    print("=" * 60)
    print(f"Engine:   {engine}")
    print(f"Volume:   {volume}%")
    print(f"Language: {language}")
    print("=" * 60)
    print()

    # Initialize the audio system
    print("Initializing audio alert system...")
    audio = AudioAlertSystem(
        enabled=True,
        engine=engine,
        volume=volume,
        language=language,
        cooldown_seconds=5,  # Short cooldown for testing
    )

    if not audio.is_ready():
        print("\n✗ Audio alert system failed to initialize.")
        print("\nTroubleshooting:")
        print("  1. Install espeak: sudo apt-get install espeak")
        print("  2. Or install pyttsx3: pip install pyttsx3")
        print("  3. Check speaker connection: speaker-test -t wav -c 2")
        print("  4. Adjust volume: alsamixer")
        return False

    print(f"✓ Audio system ready (using {audio.engine})")
    print()

    # Test 1: Basic alert
    print("Test 1: Playing test alert...")
    time.sleep(1)
    audio.test_alert()
    time.sleep(2)
    print("✓ Test alert completed")
    print()

    # Test 2: DoS alert
    print("Test 2: Simulating DoS attack alert...")
    time.sleep(1)
    audio.alert(
        alert_type="dos",
        mac_address="AA:BB:CC:DD:EE:FF",
        confidence=0.89,
        device_name="TestDevice",
    )
    time.sleep(3)
    print("✓ DoS alert completed")
    print()

    # Test 3: DDoS alert with high confidence
    print("Test 3: Simulating DDoS attack alert (high confidence)...")
    time.sleep(1)
    audio.alert(
        alert_type="ddos",
        mac_address="11:22:33:44:55:66",
        confidence=0.98,
        device_name="SuspiciousDevice",
    )
    time.sleep(3)
    print("✓ DDoS alert completed")
    print()

    # Test 4: Alert without device name (uses MAC)
    print("Test 4: Alert with MAC address only...")
    time.sleep(1)
    audio.alert(
        alert_type="dos",
        mac_address="AA:BB:CC:DD:EE:01",
        confidence=0.75,
        device_name=None,
    )
    time.sleep(3)
    print("✓ MAC-only alert completed")
    print()

    # Test 5: Cooldown test
    print("Test 5: Testing cooldown mechanism...")
    print("  Sending 3 rapid alerts (only first should play)...")
    for i in range(3):
        audio.alert(
            alert_type="dos",
            mac_address="AA:BB:CC:DD:EE:02",
            confidence=0.80,
            device_name="CooldownTest",
        )
        time.sleep(0.5)
    time.sleep(2)
    print("✓ Cooldown test completed (check that only 1 alert played)")
    print()

    # Cleanup
    audio.cleanup()

    print("=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Edit config.yaml and set audio_alerts.enabled: true")
    print("  2. Adjust volume if needed: audio_alerts.volume: 80")
    print("  3. Start the pi-agent: python run.py")
    print("  4. Trigger a DDoS test to hear real alerts")
    print()
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Test the audio alert system on Raspberry Pi",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-detect TTS engine and test
  python test_audio_alerts.py

  # Force espeak engine
  python test_audio_alerts.py --engine espeak

  # Test with different volume
  python test_audio_alerts.py --volume 100

  # Test with Spanish language
  python test_audio_alerts.py --language es --engine espeak

System requirements:
  - Raspberry Pi with speakers connected
  - espeak installed: sudo apt-get install espeak
  - Or pyttsx3 installed: pip install pyttsx3
        """,
    )
    parser.add_argument(
        "--engine",
        choices=["auto", "espeak", "pyttsx3", "gtts"],
        default="auto",
        help="TTS engine to use (default: auto)",
    )
    parser.add_argument(
        "--volume",
        type=int,
        default=80,
        help="Volume level 0-100 (default: 80)",
    )
    parser.add_argument(
        "--language",
        default="en",
        help="Language code: en, es, fr, de, etc. (default: en)",
    )
    args = parser.parse_args()

    # Validate volume
    if not 0 <= args.volume <= 100:
        print("Error: Volume must be between 0 and 100")
        sys.exit(1)

    # Run tests
    success = test_audio_system(
        engine=args.engine,
        volume=args.volume,
        language=args.language,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
