#!/bin/bash
# Check if a file was provided
if [ $# -eq 0 ]; then
    echo "Usage: md2pdf <file.md>"
    exit 1
fi

# Get the input file
INPUT="$1"

# Check if file exists
if [ ! -f "$INPUT" ]; then
    echo "Error: File '$INPUT' not found"
    exit 1
fi

# Check if file has .md extension
if [[ ! "$INPUT" =~ .md$ ]]; then
    echo "Warning: File doesn't have .md extension"
fi

# Generate output filename
OUTPUT="${INPUT%.md}.pdf"
TEMP_INPUT="/tmp/$(basename "$INPUT").processed.md"

# Preprocess the markdown to ensure proper list formatting
# This adds blank lines before and after list blocks
awk '
BEGIN { in_list = 0; prev_blank = 1 }
{
    # Check if current line is a list item
    is_list = /^[[:space:]]*[-*+][[:space:]]/
    
    # If entering a list and previous line wasnt blank, add blank line
    if (is_list && !in_list && !prev_blank) {
        print ""
    }
    
    # Print current line
    print $0
    
    # If exiting a list and current line isnt blank, prepare to add blank line
    if (!is_list && in_list && NF > 0) {
        print ""
        prev_blank = 1
    } else {
        prev_blank = (NF == 0)
    }
    
    in_list = is_list
}
' "$INPUT" > "$TEMP_INPUT"

# Run pandoc with math support
pandoc "$TEMP_INPUT" -o "$OUTPUT" \
    --pdf-engine=xelatex \
    -V mainfont="DejaVu Sans" \
    -V monofont="DejaVu Sans Mono" \
    --from markdown+tex_math_double_backslash \
    --mathjax

# Check if conversion was successful
if [ $? -eq 0 ]; then
    echo "✓ Successfully converted '$INPUT' to '$OUTPUT'"
    rm "$TEMP_INPUT"
else
    echo "✗ Conversion failed"
    echo "Processed file saved at: $TEMP_INPUT"
    exit 1
fi

