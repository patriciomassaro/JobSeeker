#!/bin/bash

output_file="all_js_ts_tsx_combined.txt"
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

# Process each file type
process_files_with_titles "js"
process_files_with_titles "ts"
process_files_with_titles "tsx"
