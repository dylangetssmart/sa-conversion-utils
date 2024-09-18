import mmap

def count_lines_mmap(file_path):
    with open(file_path, 'r') as f:
        # Memory-map the file, size 0 means whole file
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            # Count the number of newlines
            return mm.read().count(b'\n')