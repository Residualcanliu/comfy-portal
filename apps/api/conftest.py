"""让 pytest 能找到 app 包（把 apps/api 加入 sys.path）。"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
