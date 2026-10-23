"""让 pytest 能找到 app 包（把 apps/api 加入 sys.path）。"""

import os
import sys

# 测试不依赖真实部署配置：必须在导入 app 之前写入非占位值，
# 否则 settings 的占位密钥校验会在收集阶段直接报错。
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-0123456789abcdef")
os.environ.setdefault("INTERNAL_TOKEN", "test-internal-token")

sys.path.insert(0, os.path.dirname(__file__))
