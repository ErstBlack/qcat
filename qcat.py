#!/usr/bin/env python3
import os
import sys
import signal
import errno
from typing import List


def get_optimal_buffer_size(first_file_path: str) -> int:
    """
    Determine the optimal buffer size for file operations using the file system containing the first file given.

    This function attempts to get the file system block size or memory page size.
    If neither can be determined, it defaults to 4096 bytes.

    Args:
        first_file_path (str): Path to the first input file.

    Returns:
        int: The optimal buffer size in bytes.
    """
    # Try to get file system block size based on the first input file
    try:
        directory = os.path.dirname(os.path.abspath(first_file_path))
        stat = os.statvfs(directory)
        return stat.f_bsize
    except (AttributeError, OSError):
        # statvfs might not be available on all platforms or might fail
        pass

    # Try to get memory page size
    try:
        return os.sysconf("SC_PAGE_SIZE")
    except (AttributeError, ValueError):
        # sysconf might not be available or might not have SC_PAGE_SIZE
        pass

    # Default to 4096 if neither can be determined
    return 4096


def create_fifo(path: str) -> None:
    """
    Create a FIFO (named pipe) at the specified path.

    If a file already exists at the given path, it will be removed before
    creating the FIFO.

    Args:
        path (str): The path where the FIFO should be created.

    Raises:
        OSerror: If there's an error creating the FIFO.
    """
    if os.path.exists(path):
        os.unlink(path)
    try:
        os.mkfifo(path, 0o666)
    except OSError as e:
        print(f"Error creating FIFO: {e.strerror}", file=sys.stderr)
        sys.exit(1)


def write_to_fifo(input_files: List[str], output_path: str, buffer_size: int) -> None:
    """
    Write the contents of input files to the FIFO.

    This function reads from each input file in chunks and writes the data
    to the output FIFO.

    Args:
        input_files (List[str]): List of input file paths.
        output_path (str): Path to the output FIFO.
        buffer_size (int): Size of the buffer for reading/writing operations.

    Raises:
        IOError: If there's an error opening or reading from an input file.
    """
    with open(output_path, "wb") as output_file:
        for input_file_path in input_files:
            try:
                with open(input_file_path, "rb") as input_file:
                    while True:
                        buffer = input_file.read(buffer_size)
                        if not buffer:
                            break
                        output_file.write(buffer)
            except IOError as e:
                print(
                    f"Error opening input file {input_file_path}: {e.strerror}",
                    file=sys.stderr,
                )
                raise e


def merge_files(input_files: List[str], output_path: str) -> None:
    """
    Merge multiple input files into a single output file using a FIFO.

    This function creates a FIFO, forks a child process to write to the FIFO,
    and handles signals for graceful termination.

    Args:
        input_files (List[str]): List of input file paths to be merged.
        output_path (str): Path where the merged output will be written.
    """
    buffer_size = get_optimal_buffer_size(input_files[0])

    def signal_handler(signum, frame):
        """Handle SIGINT signal by removing the FIFO and exiting."""
        try:
            if os.path.exists(output_path):
                os.unlink(output_path)
        except FileNotFoundError:
            pass
        sys.exit(0)

    def child_done_handler(signum, frame):
        """Handle SIGUSR1 signal to indicate child process completion."""
        nonlocal child_done
        child_done = True

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGUSR1, child_done_handler)

    while True:
        create_fifo(output_path)
        child_done = False
        pid = os.fork()

        if pid == -1:
            print("Error forking process", file=sys.stderr)
            sys.exit(1)
        elif pid == 0:
            # Child process
            write_to_fifo(input_files, output_path, buffer_size)
            os.kill(os.getppid(), signal.SIGUSR1)
            sys.exit(0)
        else:
            # Parent process
            while not child_done:
                signal.pause()
            os.waitpid(pid, 0)
            if os.path.exists(output_path):
                os.unlink(output_path)


def main() -> None:
    """
    Main function to handle command-line arguments and initiate file merging.
    """
    if len(sys.argv) < 3:
        print(
            f"Usage: {sys.argv[0]} <output_file> <input_file1> <input_file2> ...",
            file=sys.stderr,
        )

        # Exit with code 1 if we don't receive at least 3 args
        sys.exit(1)

    output_path = sys.argv[1]
    input_files = sys.argv[2:]
    merge_files(input_files, output_path)


if __name__ == "__main__":
    main()
