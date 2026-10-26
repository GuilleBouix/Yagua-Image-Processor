"""Disable Numba's optional coverage integration in frozen Yagua builds.

An older install can leave an incomplete ``coverage`` package beside the app.
Numba imports it opportunistically and may then fail before Yagua can load the
background-removal module. Coverage instrumentation is not used by the app, so
block that optional import before any application modules are loaded.
"""

import sys

sys.modules['coverage'] = None
