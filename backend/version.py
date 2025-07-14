"""Version information for the application."""

# Version format: MAJOR.MINOR.PATCH
# - MAJOR: Incompatible API changes
# - MINOR: Added functionality in a backward-compatible manner
# - PATCH: Backward-compatible bug fixes

__version__ = "0.1.1"

# Version information as a dictionary for easier programmatic access
version_info = {
    "version": __version__,
    "major": int(__version__.split(".")[0]),
    "minor": int(__version__.split(".")[1]),
    "patch": int(__version__.split(".")[2]),
    "build_date": "2025-07-14",
    "commit_hash": ""  # Can be set during build process
}

def get_version() -> dict:
    """Return the complete version information as a dictionary."""
    return version_info
