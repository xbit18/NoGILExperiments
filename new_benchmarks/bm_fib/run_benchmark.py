import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor
import pyperf

def fib(n):
    if n < 2: return 1
    return fib(n-1) + fib(n-2)

def run_bench():
    threads = 16
        
    with ThreadPoolExecutor(max_workers=threads) as executor:
        for _ in range(threads):
            executor.submit(lambda: fib(34))

def main():
    runner = pyperf.Runner()
    runner.metadata['description'] = "Multi-thread fibonacci sequence"

    runner.bench_func('fib', run_bench)

if __name__ == "__main__":
    main()
