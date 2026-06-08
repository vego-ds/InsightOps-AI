import sys
import io
import os
import re
import traceback
import threading
import difflib
import matplotlib

matplotlib.use("Agg")  # Safe non-GUI backend
import matplotlib.pyplot as plt


class PythonInterpreterSandbox:
    def __init__(self):
        # Local variable scope for this sandbox session
        self.locals = {"plt": plt, "matplotlib": matplotlib}
        # Pre-import core data science and stats packages
        try:
            import pandas as pd
            import numpy as np
            import scipy
            import scipy.stats as stats
            import sklearn

            self.locals["pd"] = pd
            self.locals["np"] = np
            self.locals["scipy"] = scipy
            self.locals["stats"] = stats
            self.locals["sklearn"] = sklearn
        except ImportError:
            pass

        self._lock = threading.Lock()

    def load_dataframe(self, csv_path: str):
        """Pre-loads the CSV into the sandbox scope as a pandas DataFrame 'df'."""
        if "pd" in self.locals:
            pd = self.locals["pd"]
            try:
                self.locals["df"] = pd.read_csv(csv_path)
            except Exception as e:
                print(f"Error loading DataFrame in interpreter: {e}", file=sys.stderr)

    def execute(self, code: str, session_id: str, prompt: str = "") -> dict:
        """Executes code blocks with built-in agentic self-healing retries."""
        attempts = []
        current_code = code
        max_retries = 2

        for attempt in range(max_retries + 1):
            res = self._run_raw(current_code, session_id)

            if not res["error"]:
                # Success
                return {
                    "stdout": res["stdout"],
                    "stderr": res["stderr"],
                    "error": None,
                    "charts": res["charts"],
                    "attempts": attempts,
                    "code_executed": current_code,
                }

            # Record failed attempt
            attempts.append(
                {
                    "attempt": attempt + 1,
                    "failed_code": current_code,
                    "error": res["error"],
                }
            )

            if attempt == max_retries:
                break

            # Attempt code healing
            healed_code = self._heal_code(current_code, res["error"])
            if healed_code and healed_code != current_code:
                current_code = healed_code
            else:
                # Cannot heal locally, break early
                break

        # Return last failure
        return {
            "stdout": res["stdout"],
            "stderr": res["stderr"],
            "error": res["error"],
            "charts": res["charts"],
            "attempts": attempts,
            "code_executed": current_code,
        }

    def _run_raw(self, code: str, session_id: str) -> dict:
        """Executes a block of Python code, returning stdout, stderr, errors, and generated charts."""
        with self._lock:
            old_stdout = sys.stdout
            old_stderr = sys.stderr

            redirected_stdout = sys.stdout = io.StringIO()
            redirected_stderr = sys.stderr = io.StringIO()

            error_msg = None
            charts = []

            try:
                # Ensure matplotlib is cleared before running
                plt.close("all")

                # Execute the code block
                exec(code, globals(), self.locals)

                # Capture generated figures (and FuncAnimation frames if saved)
                os.makedirs("app/static/generated", exist_ok=True)
                fig_nums = plt.get_fignums()
                for i, num in enumerate(fig_nums):
                    fig = plt.figure(num)
                    chart_filename = f"chart_{session_id}_{num}_{i}.png"
                    chart_path = f"app/static/generated/{chart_filename}"
                    fig.savefig(chart_path, bbox_inches="tight", dpi=130)
                    charts.append(f"/static/generated/{chart_filename}")

                plt.close("all")

            except Exception:
                error_msg = traceback.format_exc()
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

            stdout_content = redirected_stdout.getvalue()
            stderr_content = redirected_stderr.getvalue()

            return {
                "stdout": stdout_content,
                "stderr": stderr_content,
                "error": error_msg,
                "charts": charts,
            }

    def _heal_code(self, code: str, error_msg: str) -> str | None:
        """Rule-based self-healing compiler for pandas variables and imports."""
        # 1. Handle KeyError: Column name mismatches
        if "KeyError:" in error_msg:
            # Extract key
            match = re.search(r"KeyError:\s*['\"](.*?)['\"]", error_msg)
            if match and "df" in self.locals:
                bad_col = match.group(1)
                df = self.locals["df"]
                matches = difflib.get_close_matches(
                    bad_col, df.columns, n=1, cutoff=0.3
                )
                if matches:
                    good_col = matches[0]
                    # Replace column occurrences in code
                    healed = code.replace(f"['{bad_col}']", f"['{good_col}']")
                    healed = healed.replace(f'["{bad_col}"]', f'["{good_col}"]')
                    healed = healed.replace(f".{bad_col}", f".{good_col}")
                    return healed

        # 2. Handle NameError: Missing package pre-imports
        if "NameError:" in error_msg:
            match = re.search(
                r"NameError:\s*name\s*['\"](.*?)['\"]\s*is not defined", error_msg
            )
            if match:
                name = match.group(1)
                if name == "pd":
                    return "import pandas as pd\n" + code
                if name == "np":
                    return "import numpy as np\n" + code
                if name == "plt":
                    return "import matplotlib.pyplot as plt\n" + code
                if name == "stats":
                    return "import scipy.stats as stats\n" + code

        # 3. Handle ZeroDivisionError
        if "ZeroDivisionError" in error_msg:
            # Safe division substitute
            return re.sub(
                r"/\s*([a-zA-Z0-9_\(\)\[\]\.]+)", r"/ (\1 if \1 != 0 else 1)", code
            )

        return None
