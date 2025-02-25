#!/bin/bash
# Check for required arguments
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <filepath> <output_folder>"
    exit 1
fi
filepath="$1"
output_folder="$2"

docker run --rm --gpus=all -v /home/pmarrec/vault:/data mineru:latest magic-pdf -p /data/"$filepath" -o /data/"$output_folder" -m auto



