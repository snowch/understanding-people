"""Compatibility command: the former stubs are now written reference entries."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).with_name('verify_reference_library.py')),run_name='__main__')
