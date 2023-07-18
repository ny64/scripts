#!/usr/bin/env bash

# Script: Duplicate PDF Remover
#
# Description: This script finds duplicate PDF files or files of another specified extension 
#              in a given directory or the current directory if no directory is specified.
#              Duplicates are determined by a naming scheme where duplicates
#              of a file "file.ext" are named as "file (1).ext", "file (2).ext", etc.
#              Among the duplicates, the script renames the file with the highest count
#              to the original name (e.g., "file.ext") and removes all other duplicates.
#
# Usage: ./script.sh -e [extension] [dir]
#        where [extension] is an optional argument specifying the file extension to look for
#        (without the leading dot). If no extension is specified, "pdf" is used.
#        [dir] is an optional argument specifying the directory to clean up.
#        If [dir] is not provided, the script operates on the current directory.
#
# Note: Please ensure you have a backup of your files before running the script. 
#       This script will remove files and there's no simple way to recover them.
#
# Author: Peter Breitzler
# Date: 18. Jul 2023

extension="pdf"
dir="./"

while getopts e: option
do
case "${option}"
in
e) extension=${OPTARG};;
esac
done
shift $((OPTIND -1))

if [ "$1" ]; then
  dir="$1"
fi

cd "$dir" || exit

for file in $(ls | grep -Eo '.*\s\(\d+\)\.'"$extension" | sed -E 's/ \([0-9]+\)\.'"$extension"'//g' | sort | uniq); do
  highest_count=$(ls "${file}"\ \(*."$extension" | grep -Eo '\([0-9]+\)\.'"$extension" | sed -E 's/\(([^)]+)\)\.'"$extension"'/\1/g' | sort -nr | head -n1)
  mv -v "${file} (${highest_count}).${extension}" "${file}.${extension}"
  rm -v "${file}"\ \([0-9]*\)."${extension}"
done
