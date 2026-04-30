from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "_data"
RAW_DATA_DIR = DATA_DIR / "01_raw"
INTERIM_DATA_DIR = DATA_DIR / "02_interim"
PROCESSED_DATA_DIR = DATA_DIR / "03_processed"

NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"
ARCHIVE_DIR = PROJECT_ROOT / "archive"

RAW_MEMBERSHIP_PATH = RAW_DATA_DIR / "Membership.xlsx"

FINAL_MERGED_USER_V1_PATH = PROCESSED_DATA_DIR / "final_merged_user(단칼)_v1.xlsx"
FINAL_MERGED_USER_V2_PATH = PROCESSED_DATA_DIR / "final_merged_user(단칼)_v2.xlsx"
FINAL_MERGED_USER_V3_PATH = PROCESSED_DATA_DIR / "final_merged_user(단칼)_v3.xlsx"
MEMBERSHIP_V3_PATH = PROCESSED_DATA_DIR / "Membership_v3.xlsx"


def ensure_project_dirs() -> None:
    """Create the standard project folders if they do not exist."""
    for path in [
        RAW_DATA_DIR,
        INTERIM_DATA_DIR,
        PROCESSED_DATA_DIR,
        NOTEBOOKS_DIR,
        MODELS_DIR,
        REPORTS_DIR,
        ARCHIVE_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)
