#!/bin/bash

# Script: PDF Duplicate Remover
#
# Description: This script finds duplicate PDF files in a specified directory 
#              or the current directory, if no directory is specified.
#              Duplicates are determined by a naming scheme where duplicates
#              of a file "file.pdf" are named as "file (1).pdf", "file (2).pdf", etc.
#              Among the duplicates, the script renames the file with the highest count
#              to the original name (e.g., "file.pdf") and removes all other duplicates.
#
# Usage: ./script.sh [dir]
#        where [dir] is an optional argument specifying the directory to clean up.
#        If [dir] is not provided, the script operates on the current directory.
#
# Note: Please ensure you have a backup of your files before running the script. 
#       This script will remove files and there's no simple way to recover them.
#
# Author: Peter Breitzler 
# Date: 18. Jul 2023

if [ "$1" ]; then
  dir="$1"
else
  dir="./"
fi cd "$dir" || exit

# Iterate over each unique basename of files
for file in $(ls | grep -Eo '.*\s\(\d+\)\.pdf' | sed -E 's/ \([0-9]+\)\.pdf//g' | sort | uniq); do
  # Find the file with the highest count
  highest_count=$(ls "${file}"\ \(*.pdf | grep -Eo '\([0-9]+\)\.pdf' | sed -E 's/\(([^)]+)\)\.pdf/\1/g' | sort -nr | head -n1)
  # Rename the file with the highest count to the original name
  mv -v "${file} (${highest_count}).pdf" "${file}.pdf"
  # Remove all other duplicates
  rm -v "${file}"\ \(*\).pdf
done

