import shutil
import os
import stat
from pathlib import Path
from dataclasses import dataclass
from config.settings import PROJECT_ROOT

@dataclass
class OutputDirs:
    root: Path
    screenshots: Path
    traces: Path
    videos: Path
    dashboard: Path
    logs: Path
    allure_results: Path
    auth: Path

def on_rm_error(func, path, exc_info):
    """
    Error handler for shutil.rmtree.
    If the error is due to an access error (read only file),
    it attempts to add write permission and then retries.
    If the error is for another reason it re-raises the error.
    """
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        # Fallback for aggressive file deletion
        try:
            os.remove(path)
        except Exception:
            pass

def aggressive_rmtree(dir_path: Path):
    if dir_path.exists():
        try:
            shutil.rmtree(dir_path, ignore_errors=False, onerror=on_rm_error)
        except Exception:
            # Absolute fallback if macOS locks the directory structure itself
            for item in dir_path.glob('**/*'):
                try:
                    if item.is_file():
                        item.chmod(stat.S_IWRITE)
                        item.unlink()
                except Exception:
                    pass
            try:
                shutil.rmtree(dir_path, ignore_errors=True)
            except Exception:
                pass

def create_run_dirs(run_id: str = "run_latest") -> OutputDirs:
    # 0. Legacy Wipe: Completely destroy old 'outputs' or 'artifacts' trees if they accidentally reappear
    for legacy_name in ["outputs", "artifacts"]:
        legacy_dir = PROJECT_ROOT / legacy_name
        if legacy_dir.exists():
            aggressive_rmtree(legacy_dir)
        
    parent_dir = PROJECT_ROOT / "test_runs"
    
    # 1. Dynamic Sanitation Engine: Destroy all directories that are NOT the target run_id
    if parent_dir.exists():
        for child in parent_dir.iterdir():
            if child.is_dir() and child.name != run_id:
                aggressive_rmtree(child)
                
    # 2. Clean Reconstruction
    root = parent_dir / run_id
    
    # Aggressively wipe the target root just in case
    aggressive_rmtree(root)
        
    dirs = OutputDirs(
        root=root,
        screenshots=root / "screenshots",
        traces=root / "traces",
        videos=root / "videos",
        dashboard=root / "dashboard",
        logs=root / "logs",
        allure_results=root / "allure_results",
        auth=root / "auth",
    )
    for path in (dirs.screenshots, dirs.traces, dirs.videos, dirs.dashboard, dirs.logs, dirs.allure_results, dirs.auth):
        path.mkdir(parents=True, exist_ok=True)
    return dirs
