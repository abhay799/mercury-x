# MERCURY X Step 3 Import Fix

This file adds `src` to pytest's Python path so tests can import the package as:

    mercury.contracts...

It does not make a direct project-local Python interpreter importable by
itself. Recreate or refresh the editable project installation using the
commands in `environment.md` before running:

    .\.venv\Scripts\python.exe -c "import mercury"

It does not modify any MERCURY X production contract files.
