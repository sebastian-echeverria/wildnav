from pathlib import Path
import shutil


def delete_folder(folder_path: str):
    """Removes the given folder."""
    if Path(folder_path).exists():
        shutil.rmtree(folder_path)


def create_folder(folder_path: str):
    """Creates the given folder."""
    Path(folder_path).mkdir(parents=True, exist_ok=True)
