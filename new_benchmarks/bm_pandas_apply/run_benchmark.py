import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import multiprocessing as mp
import numpy as np
import time

def long_func(s):
    for i in range(5000000):
        pass
    return s

def parallel_apply(df, func, axis=1):
    if axis == 1:
        with ThreadPoolExecutor(max_workers=mp.cpu_count()) as executor:
            results = list(executor.map(func, [row for _, row in df.iterrows()]))
        return pd.DataFrame(results, index=df.index)
    else:
        raise NotImplementedError("Only axis=1 is supported.")

df = pd.DataFrame(np.ones((500, 500), dtype=str))
start = time.time()
new_df = df.copy()
new_df.apply(long_func, axis=1)
print(time.time()-start)

start = time.time()
with ThreadPoolExecutor() as executor:
    results = list(executor.map(long_func, [row for _, row in df.iterrows()]))
parallel_df = pd.DataFrame(results, index=df.index)
print(time.time()-start)
