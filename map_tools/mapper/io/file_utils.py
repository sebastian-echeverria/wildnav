from pathlib import Path
import shutil
import os


def delete_folder_data(folder_path: str):
    """Removes the given folder."""
    if Path(folder_path).exists():
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))


def create_folder(folder_path: str):
    """Creates the given folder."""
    Path(folder_path).mkdir(parents=True, exist_ok=True)
