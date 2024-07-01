#!/bin/bash

output_file="backend_py_files.txt"
>$output_file # Empty the output file if it exists

# Function to process files and add titles
process_files_with_titles() {
	local extension=$1
	find . -type f -name "*.$extension" -not -path '*/\.*' | while read file; do
		echo "===== $file =====" >>$output_file
		cat "$file" >>$output_file
		echo "" >>$output_file # Add a newline for separation
	done
}

process_files_with_titles "py"
