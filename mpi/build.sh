#!/bin/bash
set -e
cd "$(dirname "$0")"
mpicxx -O2 -std=c++17 -ffp-contract=off -o hello hello.cpp
mpicxx -O2 -std=c++17 -ffp-contract=off -o pingpong pingpong.cpp
echo "built on $(hostname)"
