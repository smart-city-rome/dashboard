#!/bin/bash

DIR="conda_env"
PREFIX="./.conda"

if [ ! -d "$PREFIX" ]; then
    echo "Conda environment not found."
    ./create_or_sync_conda_env.sh
    exit 0
fi

mkdir -p "$DIR"

echo "Dumping conda environment to $DIR/environment.yml"
conda env export --from-history --prefix $PREFIX | sed '1d;$d' > "$DIR/environment.yml"

echo "Generating requirements.txt"
./$PREFIX/bin/pip-chill > "$DIR/requirements.txt"

echo "Environment dump complete."

