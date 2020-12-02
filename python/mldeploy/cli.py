# =============================================================================
# CLI.PY
# -----------------------------------------------------------------------------
# The execution script function for the packaged CLI.
# 
# ***This file MAY import from all other 'mldeploy' files.***
#  
# The CLI is built using the following packages:
#   - fire: Google-supported, turns functions into CLI
#   - ruamel.yaml: Edit YAML files without affecting the structure or comments.
# -----------------------------------------------------------------------------
# Author: kingfischer16 (https://github.com/kingfischer16/mldeploy)
# =============================================================================

# =============================================================================
# Imports.
# -----------------------------------------------------------------------------
import fire  # The python-fire CLI engine.
from typing import NoReturn

from .mldeploy_functions import (
    test, cwd, ls, create, build, delete
)


# =============================================================================
# Main execution function using 'fire'.
# -----------------------------------------------------------------------------
def main() -> NoReturn:
    """
    The main program function to be packaged for command line.
    """
    fire.Fire({
        'test': test,
        'cwd': cwd,
        'ls': ls,
        'create': create,
        'delete': delete,
        'build': build
    })
