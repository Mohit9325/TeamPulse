#!/usr/bin/env bash
set -e

export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
export PIP_BREAK_SYSTEM_PACKAGES=1

if [ ! -d "$HOME/venv_buildozer" ]; then
    python3 -m venv "$HOME/venv_buildozer"
fi

source "$HOME/venv_buildozer/bin/activate"
pip install --upgrade pip buildozer cython appdirs colorama jinja2 sh meson ninja build toml packaging setuptools wheel

cd /mnt/d/teampulse
buildozer -v android debug
