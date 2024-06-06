import os
import subprocess

def different():
    for version in [
        # '3.9.10',
        # 'nogil-3.9.10-1',
        # '3.9.18',
        # '3.10.13',
        '3.11.8',
        '3.12.2', 
        '3.13.0b1'
        ]:
        if version == '3.13.0b1':
            try:
                for _ in [0,1]:
                    if _ == 0:
                        version_str = version + " without GIL"
                        print(version_str) 
                        subprocess.run(f"/Users/giacomo/.pyenv/versions/{version}/bin/python /Users/giacomo/NoGILExperiments/new_benchmarks/bm_matrix_multiplication/run_benchmark_numpy.py", shell=True)
                    else: 
                        version_str = version + " with GIL"
                        print(version_str) 
                        subprocess.run(f"/Users/giacomo/.pyenv/versions/{version}/bin/python -X gil=1 /Users/giacomo/NoGILExperiments/new_benchmarks/bm_matrix_multiplication/run_benchmark_numpy.py", shell=True)
            except FileNotFoundError as e:
                print(e)
        else:
            print(version)
            try:
                subprocess.run(f"/Users/giacomo/.pyenv/versions/{version}/bin/python3 /Users/giacomo/NoGILExperiments/new_benchmarks/bm_matrix_multiplication/run_benchmark_numpy.py", shell=True)
            except FileNotFoundError as e:
                print(e)

def threads():
    version = '3.13.0b1'
    for thread in [1,2,4,8,16]:
        try:
            print(f"Nº threads: {thread}")
            subprocess.run(f"/Users/giacomo/.pyenv/versions/{version}/bin/python /Users/giacomo/NoGILExperiments/new_benchmarks/bm_matrix_multiplication/run_benchmark_numpy.py {thread}", shell=True)
        except FileNotFoundError as e:
            print(e)

if __name__ == "__main__":
    different()
    #threads()