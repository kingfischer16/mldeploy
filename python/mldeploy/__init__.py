# =============================================================================
# __INIT__.PY
# -----------------------------------------------------------------------------
# Exposes the user-level functions from the library. Allows the library
# to be used as a script instead of via the command line. Probably.
#
# -----------------------------------------------------------------------------
# Author: kingfischer16 (https://github.com/kingfischer16/mldeploy)
# =============================================================================

from .mldeploy_functions import (
    test,
    cwd,
    ls,
    create,
    build,
    delete,
    deploy,
    undeploy,
    status,
    update,
)
