# Add this after the imports section

def get_base_path() -> Path:
    """Get base path that works in both development and PyInstaller frozen apps.
    
    Returns:
        Path: Base directory path that works both in development and frozen executable
    """
    if getattr(sys, '_MEIPASS', None):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent
