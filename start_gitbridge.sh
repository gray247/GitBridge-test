#!/bin/bash
chmod 600 ~/.ssh/gitbridge_key
chmod 644 ~/.ssh/gitbridge_key.pub
chmod 600 ~/.ssh/config
python3 gitbridge.py
