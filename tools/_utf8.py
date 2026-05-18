#!/usr/bin/env python3
"""Shared import — force UTF-8 stdout/stderr on Windows to prevent GBK encoding crashes.

"""
import sys

if sys.platform == 'win32':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
