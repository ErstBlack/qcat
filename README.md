# q[uick]cat
## Description
This Python script merges multiple input files into a single output file using a FIFO (named pipe).

The script is designed to be run against files created by [split](https://man7.org/linux/man-pages/man1/split.1.html), but should also work with any group of files terminated by a newline.

## Features
- Merges multiple input files into a single output file
- Determines optimal buffer size based on the file system
- Handles signals for graceful termination
- Works with binary and text files

## Requirements
- Python 3.6 or later
- Unix-like operating system (e.g., Linux, macOS)

## Usage
Run the script from the command line with the following syntax:
```
python3 qcat.py <output_file> <input_file1> <input_file2> ...
```

e.g.
```
python3 qcat.py merged_output.img split-file.img1 split-file.img2 split-file.img2
```

The output file can the be treated as a normal file for most intents and purposes.
