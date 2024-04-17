import sys
import multiprocessing as mp
import time
from concurrent.futures import ThreadPoolExecutor
import tracemalloc
import sys

#print(f"NoGil: {getattr(sys.flags, 'nogil', False)}")
#print(f"Cores: {mp.cpu_count()}")
def fib(n):
    if n < 2: return 1
    return fib(n-1) + fib(n-2)

threads = 1
if len(sys.argv) > 1:
    threads = int(sys.argv[1])
    
start_time = time.time()
tracemalloc.start()
with ThreadPoolExecutor(max_workers=threads) as executor:
    for _ in range(threads):
        executor.submit(lambda: fib(34))
snapshot = tracemalloc.take_snapshot()
if len(sys.argv) > 2:
    snapshot.dump(f"{sys.argv[2]}.tracemalloc")
_, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()

total_time = round(time.time()-start_time, 3)
print(total_time, peak)
