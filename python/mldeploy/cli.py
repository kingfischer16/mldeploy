# =============================================================================
# CLI.PY
# -----------------------------------------------------------------------------
# The execution script function for the packaged CLI.
#
# ***This file MUST ONLY import from 'mldeply_functions.py'.***
#
# The CLI is built using the following packages:
#   - fire: Google-supported, turns functions into CLI
# -----------------------------------------------------------------------------
# Author: kingfischer16 (https://github.com/kingfischer16/mldeploy)
# =============================================================================

# =============================================================================
# Imports.
# -----------------------------------------------------------------------------
import fire  # The python-fire CLI engine.
from typing import NoReturn

from .mldeploy_functions import test, cwd, ls, create, build, delete


# =============================================================================
# Main execution function using 'fire'.
# -----------------------------------------------------------------------------
def main() -> NoReturn:
    """
    The main program function to be packaged for command line.

    This function uses python-fire to convert the specified functions
    into
    """
    fire.Fire(
        {
            "test": test,
            "cwd": cwd,
            "ls": ls,
            "create": create,
            "delete": delete,
            "build": build,
        }
    )
