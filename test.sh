#!/bin/bash
set -e 
source .venv/bin/activate
overpass-ql-check --test
