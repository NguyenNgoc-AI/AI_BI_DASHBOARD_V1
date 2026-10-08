"""Keep temporary test artifacts inside the project on restricted Windows hosts."""

import os
import tempfile
from pathlib import Path


TEST_TEMP = Path(__file__).resolve().parents[1] / ".test-temp"
TEST_TEMP.mkdir(exist_ok=True)
os.environ["TEMP"] = str(TEST_TEMP)
os.environ["TMP"] = str(TEST_TEMP)
tempfile.tempdir = str(TEST_TEMP)
