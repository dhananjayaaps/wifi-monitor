"""Audio alert system for DDoS/DoS detection notifications.

Plays voice alerts through connected speakers when attacks are detected.
Uses multiple TTS engines with fallback support for Raspberry Pi.
"""

from __future__ import annotations

import logging
import os
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class AudioAlertSystem:
    """Manages audio alerts for security incidents."""

    def __init__(
        self,
        enabled: bool = False,
        engine: str = "auto",
        volume: int = 80,
        language: str = "en",
        cooldown_seconds: int = 60,
    ):
        """
        Initialize the audio alert system.

        Args:
            enabled: Enable/disable audio alerts
            engine: TTS engine to use ('auto', 'espeak', 'pyttsx3', 'gtts')
            volume: Volume level 0-100 (for espeak/amixer)
            language: Language code (e.g., 'en', 'es', 'fr')
            cooldown_seconds: Minimum seconds between alerts of the same type
        """
        self.enabled = enabled
        self.engine = engine
        self.volume = max(0, min(100, volume))
        self.language = language
        self.cooldown_seconds = cooldown_seconds

        self._tts_engine = None
        self._last_alert_time = {}
        self._alert_queue = []
        self._lock = threading.Lock()

        if self.enabled:
            self._initialize_tts()

    def _initialize_tts(self) -> None:
        """Detect and initialize the best available TTS engine."""
        if self.engine == "auto":
            # Try engines in order of preference for Raspberry Pi
            if self._check_espeak():
                self.engine = "espeak"
                logger.info("Audio alerts: using espeak (native)")
            elif self._check_pyttsx3():
                self.engine = "pyttsx3"
                logger.info("Audio alerts: using pyttsx3")
            elif self._check_gtts():
                self.engine = "gtts"
                logger.info("Audio alerts: using gTTS (requires internet)")
            else:
                logger.warning(
                    "No TTS engine available. Install espeak: sudo apt-get install espeak"
                )
                self.enabled = False
                return
        else:
            # Use specified engine
            logger.info(f"Audio alerts: using {self.engine}")

        # Set system volume for Linux/Raspberry Pi
        self._set_volume()

    def _check_espeak(self) -> bool:
        """Check if espeak is available (best for Raspberry Pi)."""
        try:
            result = subprocess.run(
                ["which", "espeak"],
                capture_output=True,
                timeout=2,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _check_pyttsx3(self) -> bool:
        """Check if pyttsx3 is available."""
        try:
            import pyttsx3
            return True
        except ImportError:
            return False

    def _check_gtts(self) -> bool:
        """Check if gTTS is available."""
        try:
            from gtts import gTTS
            return True
        except ImportError:
            return False

    def _set_volume(self) -> None:
        """Set system volume on Linux/Raspberry Pi."""
        try:
            # Try amixer (most common on Raspberry Pi)
            subprocess.run(
                ["amixer", "sset", "PCM", f"{self.volume}%"],
                capture_output=True,
                timeout=2,
            )
            logger.debug(f"Set volume to {self.volume}%")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # amixer not available, volume control will be manual
            pass

    def is_ready(self) -> bool:
        """Check if the audio system is ready to play alerts."""
        return self.enabled

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def alert(
        self,
        alert_type: str,
        mac_address: str,
        confidence: float,
        device_name: Optional[str] = None,
    ) -> None:
        """
        Play an audio alert for a detected attack.

        Args:
            alert_type: 'dos' or 'ddos'
            mac_address: MAC address of the attacker/victim
            confidence: Detection confidence (0-1)
            device_name: Optional friendly device name
        """
        if not self.is_ready():
            return

        # Check cooldown
        import time
        now = time.time()
        key = f"{alert_type}_{mac_address}"
        with self._lock:
            last_time = self._last_alert_time.get(key, 0)
            if now - last_time < self.cooldown_seconds:
                logger.debug(f"Alert cooldown active for {key}, skipping audio")
                return
            self._last_alert_time[key] = now

        # Build alert message
        message = self._build_message(alert_type, mac_address, confidence, device_name)

        # Play in background thread to avoid blocking
        thread = threading.Thread(
            target=self._play_alert,
            args=(message,),
            daemon=True,
        )
        thread.start()

    def test_alert(self) -> None:
        """Play a test alert to verify audio is working."""
        if not self.is_ready():
            logger.warning("Audio alerts not enabled or no TTS engine available")
            return

        message = "Audio alert system test. Security monitoring is active."
        self._play_alert(message)

    # -------------------------------------------------------------------------
    # TTS implementations
    # -------------------------------------------------------------------------

    def _play_alert(self, message: str) -> None:
        """Play the alert using the configured TTS engine."""
        try:
            if self.engine == "espeak":
                self._play_espeak(message)
            elif self.engine == "pyttsx3":
                self._play_pyttsx3(message)
            elif self.engine == "gtts":
                self._play_gtts(message)
            else:
                logger.error(f"Unknown TTS engine: {self.engine}")
        except Exception as e:
            logger.error(f"Failed to play audio alert: {e}", exc_info=True)

    def _play_espeak(self, message: str) -> None:
        """Play alert using espeak (fastest, best for Raspberry Pi)."""
        try:
            # espeak parameters:
            # -v: voice/language
            # -s: speed (words per minute, default 175)
            # -a: amplitude (volume 0-200, default 100)
            subprocess.run(
                ["espeak", "-v", self.language, "-s", "150", "-a", "200", message],
                capture_output=True,
                timeout=30,
                check=True,
            )
            logger.info(f"Audio alert played: {message[:50]}...")
        except subprocess.TimeoutExpired:
            logger.error("espeak timeout")
        except subprocess.CalledProcessError as e:
            logger.error(f"espeak failed: {e}")

    def _play_pyttsx3(self, message: str) -> None:
        """Play alert using pyttsx3 (offline, cross-platform)."""
        try:
            import pyttsx3

            engine = pyttsx3.init()
            engine.setProperty("rate", 150)  # Speed
            engine.setProperty("volume", self.volume / 100)

            # Set voice to match language if available
            voices = engine.getProperty("voices")
            for voice in voices:
                if self.language in voice.id.lower():
                    engine.setProperty("voice", voice.id)
                    break

            engine.say(message)
            engine.runAndWait()
            logger.info(f"Audio alert played: {message[:50]}...")
        except Exception as e:
            logger.error(f"pyttsx3 failed: {e}")

    def _play_gtts(self, message: str) -> None:
        """Play alert using gTTS (requires internet, high quality)."""
        try:
            from gtts import gTTS
            import pygame

            # Generate speech
            tts = gTTS(text=message, lang=self.language, slow=False)

            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as fp:
                temp_path = fp.name
                tts.save(temp_path)

            # Play using pygame (most compatible on Raspberry Pi)
            try:
                pygame.mixer.init()
                pygame.mixer.music.load(temp_path)
                pygame.mixer.music.set_volume(self.volume / 100)
                pygame.mixer.music.play()

                # Wait for playback to finish
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)

                pygame.mixer.quit()
                logger.info(f"Audio alert played: {message[:50]}...")
            except Exception as e:
                # Fallback: use system player
                logger.debug(f"pygame failed, trying system player: {e}")
                self._play_with_system_player(temp_path)
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass

        except Exception as e:
            logger.error(f"gTTS failed: {e}")

    def _play_with_system_player(self, audio_path: str) -> None:
        """Fallback: play audio file using system player."""
        players = ["mpg123", "mpg321", "ffplay", "aplay"]
        for player in players:
            try:
                subprocess.run(
                    [player, audio_path],
                    capture_output=True,
                    timeout=30,
                    check=True,
                )
                return
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                continue

        logger.error("No audio player available")

    # -------------------------------------------------------------------------
    # Message templates
    # -------------------------------------------------------------------------

    def _build_message(
        self,
        alert_type: str,
        mac_address: str,
        confidence: float,
        device_name: Optional[str],
    ) -> str:
        """Build the alert message text."""
        attack_name = "denial of service" if alert_type == "dos" else "distributed denial of service"
        confidence_pct = int(confidence * 100)

        # Shorten MAC for voice (speak last 4 chars only)
        mac_short = mac_address.replace(":", "").upper()[-4:]

        device_str = device_name if device_name else f"device ending in {mac_short}"

        # Build message variants based on confidence
        if confidence >= 0.95:
            urgency = "Critical security alert."
        elif confidence >= 0.85:
            urgency = "Security alert."
        else:
            urgency = "Security warning."

        message = (
            f"{urgency} {attack_name.upper()} attack detected from {device_str}. "
            f"Confidence: {confidence_pct} percent. Immediate action recommended."
        )

        return message

    def cleanup(self) -> None:
        """Clean up resources."""
        # Nothing to clean up currently, but kept for future use
        pass
