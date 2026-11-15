"""Create a ZIP of the committed project source from the current revision."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
ARCHIVE = ROOT / "dark-matter-research-source.zip"
subprocess.run(["git", "archive", "--format=zip", "--prefix=dark-matter-research/",
                "-o", str(ARCHIVE), "HEAD"], cwd=ROOT, check=True)
print(ARCHIVE)
