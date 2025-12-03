"""Cross-platform directory paths using XDG conventions.

Uses platformdirs to provide appropriate paths on:
- Linux: XDG Base Directory Specification (~/.config, ~/.local/share, etc.)
- macOS: ~/Library/Application Support
- Windows: %LOCALAPPDATA% or %APPDATA%

The XDG environment variables are respected on all platforms:
- XDG_CONFIG_HOME: Override config directory
- XDG_DATA_HOME: Override data directory
- XDG_STATE_HOME: Override state directory
- XDG_CACHE_HOME: Override cache directory
"""

from pathlib import Path

from platformdirs import PlatformDirs

# Application identifiers
APP_NAME = "gmail-ai-unsub"
APP_AUTHOR = "gmail-ai-unsub"  # Used on Windows for nested directories

# Create platform dirs instance
_dirs = PlatformDirs(APP_NAME, APP_AUTHOR, ensure_exists=False)


def get_config_dir(ensure_exists: bool = False) -> Path:
    """Get the configuration directory.

    Returns:
        Path to config directory:
        - Linux: ~/.config/gmail-ai-unsub (or $XDG_CONFIG_HOME/gmail-ai-unsub)
        - macOS: ~/Library/Application Support/gmail-ai-unsub
        - Windows: C:\\Users\\<user>\\AppData\\Local\\gmail-ai-unsub\\gmail-ai-unsub

    Args:
        ensure_exists: If True, create the directory if it doesn't exist
    """
    path = Path(_dirs.user_config_dir)
    if ensure_exists:
        path.mkdir(parents=True, exist_ok=True)
    return path


def get_data_dir(ensure_exists: bool = False) -> Path:
    """Get the data directory for application data.

    Returns:
        Path to data directory:
        - Linux: ~/.local/share/gmail-ai-unsub (or $XDG_DATA_HOME/gmail-ai-unsub)
        - macOS: ~/Library/Application Support/gmail-ai-unsub
        - Windows: C:\\Users\\<user>\\AppData\\Local\\gmail-ai-unsub\\gmail-ai-unsub

    Args:
        ensure_exists: If True, create the directory if it doesn't exist
    """
    path = Path(_dirs.user_data_dir)
    if ensure_exists:
        path.mkdir(parents=True, exist_ok=True)
    return path


def get_state_dir(ensure_exists: bool = False) -> Path:
    """Get the state directory for runtime state (like state.json).

    Returns:
        Path to state directory:
        - Linux: ~/.local/state/gmail-ai-unsub (or $XDG_STATE_HOME/gmail-ai-unsub)
        - macOS: ~/Library/Application Support/gmail-ai-unsub
        - Windows: C:\\Users\\<user>\\AppData\\Local\\gmail-ai-unsub\\gmail-ai-unsub

    Args:
        ensure_exists: If True, create the directory if it doesn't exist
    """
    path = Path(_dirs.user_state_dir)
    if ensure_exists:
        path.mkdir(parents=True, exist_ok=True)
    return path


def get_cache_dir(ensure_exists: bool = False) -> Path:
    """Get the cache directory.

    Returns:
        Path to cache directory:
        - Linux: ~/.cache/gmail-ai-unsub (or $XDG_CACHE_HOME/gmail-ai-unsub)
        - macOS: ~/Library/Caches/gmail-ai-unsub
        - Windows: C:\\Users\\<user>\\AppData\\Local\\gmail-ai-unsub\\gmail-ai-unsub\\Cache

    Args:
        ensure_exists: If True, create the directory if it doesn't exist
    """
    path = Path(_dirs.user_cache_dir)
    if ensure_exists:
        path.mkdir(parents=True, exist_ok=True)
    return path


def get_config_file() -> Path:
    """Get the default config file path.

    Returns:
        Path to config.toml in the config directory
    """
    return get_config_dir() / "config.toml"


def get_state_file() -> Path:
    """Get the default state file path.

    Returns:
        Path to state.json in the state directory
    """
    return get_state_dir() / "state.json"


def get_token_file() -> Path:
    """Get the default OAuth token file path.

    Returns:
        Path to token.json in the data directory
    """
    return get_data_dir() / "token.json"


# Legacy path for backwards compatibility
def get_legacy_config_dir() -> Path:
    """Get the legacy config directory (~/.gmail-ai-unsub).

    Used for migration from older versions.
    """
    return Path.home() / ".gmail-ai-unsub"


def find_config_file() -> Path | None:
    """Find the config file, checking multiple locations.

    Search order:
    1. Current directory (./config.toml)
    2. XDG config directory
    3. Legacy home directory (~/.gmail-ai-unsub/config.toml)

    Returns:
        Path to config file if found, None otherwise
    """
    # Check current directory first
    cwd_config = Path.cwd() / "config.toml"
    if cwd_config.exists():
        return cwd_config

    # Check XDG config directory
    xdg_config = get_config_file()
    if xdg_config.exists():
        return xdg_config

    # Check legacy location
    legacy_config = get_legacy_config_dir() / "config.toml"
    if legacy_config.exists():
        return legacy_config

    return None
