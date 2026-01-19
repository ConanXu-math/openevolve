#!/usr/bin/env python
"""
Entry point script for OpenEvolve
"""
import os
# 避免本地 Ollama 请求被代理拦截
os.environ.setdefault("NO_PROXY", "localhost,127.0.0.1")

import sys
from openevolve.cli import main

if __name__ == "__main__":
    sys.exit(main())
