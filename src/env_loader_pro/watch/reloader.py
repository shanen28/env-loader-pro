"""Live reloading support for configuration changes."""

import threading
import time
from pathlib import Path
from typing import Callable, Optional

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = None


class ConfigReloader:
    """Manages live reloading of configuration files."""
    
    def __init__(
        self,
        config_path: str,
        reload_callback: Callable[[], None],
        poll_interval: float = 1.0,
    ):
        """Initialize config reloader.
        
        Args:
            config_path: Path to .env file to watch
            reload_callback: Callback function to call on reload
            poll_interval: Polling interval in seconds (if watchdog unavailable)
        """
        if not WATCHDOG_AVAILABLE:
            raise ImportError(
                "watchdog is required for live reloading. "
                "Install with: pip install env-loader-pro[watch]"
            )
        
        self.config_path = Path(config_path)
        self.reload_callback = reload_callback
        self.poll_interval = poll_interval
        self.observer: Optional[Observer] = None
        self._running = False
        self._last_modified = 0
    
    def start(self) -> None:
        """Start watching for file changes."""
        if self._running:
            return
        
        self._running = True
        
        if WATCHDOG_AVAILABLE:
            self._start_watchdog()
        else:
            self._start_polling()
    
    def stop(self) -> None:
        """Stop watching for file changes."""
        self._running = False
        
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
    
    def _start_watchdog(self) -> None:
        """Start using watchdog for file system events."""
        class ConfigFileHandler(FileSystemEventHandler):
            def __init__(self, reloader):
                self.reloader = reloader
            
            def on_modified(self, event):
                if not event.is_directory:
                    if Path(event.src_path) == self.reloader.config_path:
                        self.reloader._trigger_reload()
        
        event_handler = ConfigFileHandler(self)
        self.observer = Observer()
        self.observer.schedule(
            event_handler,
            path=str(self.config_path.parent),
            recursive=False
        )
        self.observer.start()
    
    def _start_polling(self) -> None:
        """Start polling-based file watching (fallback)."""
        def poll_loop():
            while self._running:
                try:
                    if self.config_path.exists():
                        current_modified = self.config_path.stat().st_mtime
                        if current_modified > self._last_modified:
                            self._last_modified = current_modified
                            self._trigger_reload()
                except Exception:
                    pass
                
                time.sleep(self.poll_interval)
        
        thread = threading.Thread(target=poll_loop, daemon=True)
        thread.start()
    
    def _trigger_reload(self) -> None:
        """Trigger configuration reload."""
        try:
            self.reload_callback()
        except Exception as e:
            from ..utils.logging import get_logger
            logger = get_logger()
            logger.error(f"Reload callback failed: {e}")


def create_reloader(
    config_path: str,
    reload_callback: Callable[[], None],
    poll_interval: float = 1.0,
) -> Optional[ConfigReloader]:
    """Create a config reloader if watchdog is available.
    
    Args:
        config_path: Path to .env file
        reload_callback: Callback function
        poll_interval: Polling interval
    
    Returns:
        ConfigReloader instance or None if watchdog unavailable
    """
    if not WATCHDOG_AVAILABLE:
        return None
    
    return ConfigReloader(config_path, reload_callback, poll_interval)
