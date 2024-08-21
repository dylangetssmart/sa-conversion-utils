import pandas as pd
import time

file_path = "C:\\LocalConv\\Litify-Shiner\\data\\Event.csv"
chunk_sizes = [500, 1000, 2000, 5000, 10000]

for size in chunk_sizes:
    start_time = time.time()
    
    for chunk in pd.read_csv(file_path, chunksize=size):
        # Process chunk (e.g., insert into database)
        pass

    end_time = time.time()
    duration = end_time - start_time
    print(f"Chunk size {size} took {duration:.2f} seconds")
