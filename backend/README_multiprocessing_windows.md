# Multiprocessing with Flask on Windows: Required Refactor

## Problem

On Windows, Python's multiprocessing primitives (Manager, Pool, Queue) **must be created in the main process** (inside `if __name__ == "__main__":`). Creating them at import time or in code that runs during module import (such as at the top level of a Flask app) will cause deadlocks, hangs, or silent failures.

## Symptoms

- The app hangs or blocks when starting a multiprocessing task.
- No logs are produced from worker processes.
- Restarting the task in VSCode "unblocks" it for a moment.
- You see:  
  ```
  RuntimeError: Multiprocessing primitives must be created in the main process on Windows.
  ```

## Solution

**You must refactor your Flask app so that all multiprocessing primitives are created only in the main process.**

### Step-by-step Fix

1. **Move multiprocessing initialization into the main block.**

   In your `backend/app.py` (or wherever your Flask app is started), ensure you have:

   ```python
   if __name__ == "__main__":
       from backend.routes.file_processing_routes import init_multiprocessing
       init_multiprocessing()  # Only here!
       app.run(...)
   ```

2. **Remove any top-level or import-time creation of Manager, Pool, or SessionStore.**
   - Do not create these at the module level in `file_processing_routes.py`.
   - Only create them after the app is running in the main process.

3. **Defer SessionStore and session creation until after multiprocessing is initialized.**
   - If you need a global SessionStore, initialize it after `init_multiprocessing()` in the main block, or use a factory function to create it on demand.

4. **Example main block:**

   ```python
   # backend/app.py
   from flask import Flask
   from backend.routes.file_processing_routes import file_bp, init_multiprocessing, SessionStore

   app = Flask(__name__)
   app.register_blueprint(file_bp)

   if __name__ == "__main__":
       init_multiprocessing()
       sessions = SessionStore()  # Now safe
       app.run(debug=True)
   ```

5. **Update all code to use the `sessions` object created in the main block, not at import time.**

## References

- [Python multiprocessing docs](https://docs.python.org/3/library/multiprocessing.html#contexts-and-start-methods)
- [Flask + multiprocessing on Windows issues](https://github.com/pallets/flask/issues/3351)

---

**Summary:**  
All multiprocessing primitives must be created only in the main process on Windows. Refactor your Flask app to ensure this, and your "silent failure" and deadlock issues will be resolved.
