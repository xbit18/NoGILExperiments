import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import multiprocessing as mp
import numpy as np
import pyperf

def copy_row(row):
    return [int(value + 0) for value in row]

def long_func(s):
    s = copy_row(s)
    for i in range(len(list(s))):
        for j in range(2000):
            s[i] = s[i] + 1
    return s

def run_bench():
    df = pd.DataFrame(np.ones((500, 500), dtype=int))
    
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(long_func, [row for _, row in df.iterrows()]))
    parallel_df = pd.DataFrame(results, index=df.index)

def main():
    runner = pyperf.Runner()
    runner.metadata['description'] = "Parallel pandas apply"

    runner.bench_func('pandas_apply', run_bench)

if __name__ == "__main__":
    main()
