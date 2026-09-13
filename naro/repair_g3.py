from __future__ import annotations

import importlib
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

DEFAULT_ROOT = Path(r"D:\\NARO_LINKED_CLIENT_BASELINE\\NARO_CP41_CORE_BASELINE_RESPONSIVE_UI")
ROOT = Path(os.environ.get("NARO_ROOT") or DEFAULT_ROOT).resolve()
SYSTEM = ROOT / "_system"
UPDATER = SYSTEM / "naro_updater.py"
RESULT = ROOT / "data" / "NARO_LINK_REPAIR_G3_RESULT.txt"

def write_result(text: str) -> None:
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(text, encoding="utf-8")

def fail(message: str, code: int = 2) -> None:
    write_result("FAILED\n" + message + "\n")
    print("FAILED:", message)
    raise SystemExit(code)

if not UPDATER.exists():
    fail(f"NARO updater not found: {UPDATER}")

stamp = time.strftime("%Y%m%d-%H%M%S")
backup_dir = ROOT / "data" / "naro_link_bootstrap_backup_g3" / stamp
backup_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(UPDATER, backup_dir / "naro_updater.py.before_g3")

text = UPDATER.read_text(encoding="utf-8")
if 'manifest_url = UPDATE_MANIFEST_URL + separator + "ts="' not in text:
    pattern = re.compile(
        r'def _fetch_manifest\(\) -> dict\[str, Any\]:\s*\n'
        r'\s*raw = _request_bytes\(\s*\n'
        r'\s*UPDATE_MANIFEST_URL,\s*\n'
        r'\s*max_bytes=512 \* 1024,\s*\n'
        r'\s*timeout=max\(UPDATE_CONNECT_TIMEOUT, 1\),\s*\n'
        r'\s*\)\s*\n',
        re.MULTILINE,
    )
    replacement = (
        'def _fetch_manifest() -> dict[str, Any]:\n'
        '    separator = "&" if "?" in UPDATE_MANIFEST_URL else "?"\n'
        '    manifest_url = UPDATE_MANIFEST_URL + separator + "ts=" + str(int(time.time()))\n'
        '    raw = _request_bytes(\n'
        '        manifest_url,\n'
        '        max_bytes=512 * 1024,\n'
        '        timeout=max(UPDATE_CONNECT_TIMEOUT, 1),\n'
        '    )\n'
    )
    new_text, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        fail("Could not patch the updater manifest request safely.")
    UPDATER.write_text(new_text, encoding="utf-8")

patched = UPDATER.read_text(encoding="utf-8")
if 'manifest_url = UPDATE_MANIFEST_URL + separator + "ts="' not in patched:
    fail("Updater patch verification failed.")

sys.path.insert(0, str(SYSTEM))
importlib.invalidate_caches()
sys.modules.pop("naro_updater", None)

try:
    from naro_updater import check_and_apply_updates
    result = check_and_apply_updates(ROOT)
except Exception as exc:
    fail(f"Updater execution failed: {type(exc).__name__}: {exc}")

state_path = ROOT / "data" / "naro_update_state.json"
build_path = ROOT / "BUILD_INFO.txt"
state = {}
if state_path.exists():
    state = json.loads(state_path.read_text(encoding="utf-8"))
build = build_path.read_text(encoding="utf-8", errors="replace") if build_path.exists() else ""

summary = (
    f"checked={result.checked}\n"
    f"applied={result.applied}\n"
    f"release_id={result.release_id}\n"
    f"generation={result.generation}\n"
    f"changed_files={result.changed_files}\n"
    f"message={result.message}\n"
    f"state_generation={state.get('generation')}\n"
    f"state_release={state.get('release_id')}\n"
)

if int(state.get("generation") or 0) >= 3 and "Linked Update Validation: G3" in build:
    write_result("SUCCESS\n" + summary)
    print("SUCCESS: NARO linked updater reached G3.")
    print(summary)
    raise SystemExit(0)

write_result("FAILED_AFTER_REPAIR\n" + summary)
print("FAILED_AFTER_REPAIR")
print(summary)
raise SystemExit(3)
