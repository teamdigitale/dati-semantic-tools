#!/usr/bin/bash
#
# Validate .ttl files with pyshacl.
#
for file in "$@"; do

	echo "Processing $file"
	python -mpyshacl "$file"
	# echo "Error processing: $file" >&2
done
