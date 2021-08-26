#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
~/.virtualenvs/ulogme/bin/python -u "$SCRIPT_DIR/log.py"