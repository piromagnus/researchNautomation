#!/bin/bash
# Check for required arguments
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <filepath> <output_folder>"
    exit 1
fi

ROOT_DIR="/home/pmarrec/vault"
filepath="$1"
output_folder="$2"

docker run --rm --gpus=all -v $ROOT_DIR:/data mineru:latest magic-pdf -p /data/"$filepath" -o /data/"$output_folder" -m auto

