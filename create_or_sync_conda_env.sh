#!/bin/bash

DIR="conda_env"
PREFIX="./.conda"

if command -v tput >/dev/null 2>&1 && [ -t 1 ]; then
    BOLD="$(tput bold)"; RESET="$(tput sgr0)"
    GREEN="$(tput setaf 2)"; YELLOW="$(tput setaf 3)"; CYAN="$(tput setaf 6)"
else
    BOLD=""; RESET=""; GREEN=""; YELLOW=""; CYAN=""
fi

function final_recommendations {
    echo
    printf "%s%s%s\n" "${BOLD}${GREEN}" "Environment setup complete." "${RESET}"
    printf "%s%s%s\n" "${CYAN}" "To activate the conda environment, run:" "${RESET}"
    printf "  %s%s%s\n" "${BOLD}${YELLOW}" "conda activate $PREFIX" "${RESET}"
    echo
}

# if PREFIX dir exists update, otherwise create
if [ -d "$PREFIX" ]; then
    echo "Updating existing conda environment at $PREFIX"
    conda env update --prefix $PREFIX -f $DIR/environment.yml
    ./$PREFIX/bin/pip install -r $DIR/requirements.txt
else
    echo "Creating new conda environment at $PREFIX"
    if [ -d "$DIR" ]; then
        conda env create --prefix $PREFIX -f $DIR/environment.yml
        ./$PREFIX/bin/pip install -r $DIR/requirements.txt
    else
        echo "${BOLD}${YELLOW}Detecting available Python versions...${RESET}"
        mapfile -t PY_VERSIONS < <(
            conda search -f python 2>/dev/null \
            | awk '$1=="python"{print $2}' \
            | awk -F. 'NF>=2{print $1"."$2}' \
            | sort -u -V
        )

        if [ ${#PY_VERSIONS[@]} -eq 0 ]; then
            read -p "${BOLD}${YELLOW}Enter the Python version (e.g. 3.8): ${RESET}" PYTHON_VERSION
        else
            echo "${BOLD}${YELLOW}Select a Python version:${RESET}"
            OPTIONS=("${PY_VERSIONS[@]}" "Other...")
            PS3="${BOLD}${YELLOW}Enter choice [1-${#OPTIONS[@]}]: ${RESET}"
            select opt in "${OPTIONS[@]}"; do
                if [ -n "$opt" ]; then
                    if [ "$opt" = "Other..." ]; then
                        read -p "${BOLD}${YELLOW}Enter the Python version (e.g. 3.8): ${RESET}" PYTHON_VERSION
                    else
                        PYTHON_VERSION="$opt"
                    fi
                    break
                else
                    echo "${YELLOW}Invalid selection.${RESET}"
                fi
            done
        fi

        if ! [[ $PYTHON_VERSION =~ ^[0-9]+\.[0-9]+$ ]]; then
            echo "${BOLD}${YELLOW}Invalid Python version format. Please use 'X.Y' format.${RESET}"
        else
            conda create --prefix "$PREFIX" "python=$PYTHON_VERSION" -y
            ./$PREFIX/bin/pip install pip-chill
        fi
        ./dump_conda_env.sh
    fi
fi

echo "*" > "$PREFIX/.gitignore"

final_recommendations
