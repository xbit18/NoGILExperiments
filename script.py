#!/usr/bin/env python3

# Setup steps
# Importa librerie
import multiprocessing
import sys
import os
import csv
import pandas as pd
import numpy as np
import json
from pprint import pprint as pp
import matplotlib.pyplot as plt
import subprocess

# Installa versioni di python necessarie


def check_file(versions):
    if os.path.exists("./versions.json"):
        with open("./versions.json","r") as f:
            versions = json.load(f)
            print("loaded")
    else:
        with open("./versions.json","w") as f:
            versions_json = json.dumps(versions, indent=4)
            f.write(versions_json)
            print("dumped")


# Metodo che controlla che ogni versione specificata sia installata sul sistema.
# Se non lo è la installa, e se il processo di installazione fallisce skippa
# quella versione rimuovendola dall'elenco di versioni da testare.


def check_versions(versions):
    temp = versions.copy()
    for version in temp.keys():
        if not os.path.exists(f"{os.environ['HOME']}/.pyenv/versions/{version}"):
            res1 = subprocess.run(f"env PYTHON_CONFIGURE_OPTS='--enable-optimizations --with-lto' pyenv install {version}", shell=True)
        res2 = subprocess.run(f"{os.environ['HOME']}/.pyenv/versions/{version}/bin/python -m pip install pyperformance", shell=True, capture_output=True)


# Test single thread
def single_thread(versions):
    #print("\n###### Tuning system for tests ######")
    subprocess.run("pyperf system tune", shell=True)

    for version, done in versions.items():
        if done[0]:
            continue

        command = f"pyperformance run --python={os.environ['HOME']}/.pyenv/versions/{version}/bin/python -o ./pyperf_res/{version}.json"
        subprocess.run(
            command,
            shell=True)

        versions[version][0] = True
        with open("./versions.json", "w") as f:
            versions_json = json.dumps(versions, indent=4)
            f.write(versions_json)

    subprocess.run("pyperf system reset", shell=True)


def memory_single_thread(versions):
    # print("\n###### Tuning system for tests ######")
    subprocess.run("pyperf system tune", shell=True)

    for version, done in versions.items():
        if done[1]:
            continue

        command = f"{os.environ['HOME']}/.pyenv/versions/{version}/bin/python -m pyperformance run -m -o ./pyperf_res/memory/{version}.json"
        subprocess.run(
            command,
            shell=True)

        versions[version][1] = True
        with open("./versions.json", "w") as f:
            versions_json = json.dumps(versions, indent=4)
            f.write(versions_json)

    subprocess.run("pyperf system reset", shell=True)

# Test multi thread
# Variabili per definire quanti thread e quanti loop per thread
def exec_threads(version):
    global THREADS, LOOPS_PER_THREAD
    times = []
    for threads in range(1,THREADS+1):
        print(f"Current version: {version}")
        print("Threads:", threads)
        all_time=0
        for i in range(LOOPS_PER_THREAD):
            output = subprocess.check_output(f"~/.pyenv/versions/{version}/bin/python fib.py {threads}", shell=True)
            all_time += float(output.decode(sys.stdout.encoding).replace('\n',''))
        times.append(round(all_time/LOOPS_PER_THREAD, ndigits=3))
    return times


def save_res(version, times):
    with open("times.csv", "a") as csv_file:
            writer = csv.writer(csv_file, delimiter=',')
            to_insert = []
            to_insert.append(version)
            to_insert.extend(times[version])
            writer.writerow(to_insert)


def multi_thread(versions):
    THREADS = 50
    LOOPS_PER_THREAD = 10

    times = {}
    for version, done in versions.items():
        if done[2]:
            continue

        # Se non è nogil calcola i tempi normalmente
        if version != "nogil-3.9.10-1":
            res = exec_threads(version)
            times[f"{version}"] = res
            save_res(version, times)

        # Altrimenti calcolali sia con PYTHONGIL=0 che PYTHONGIL=1
        else:
            for val in [0, 1]:
                os.environ["PYTHONGIL"] = str(val)
                version_str = f"3.9.10-nogil-{val}"
                tms = exec_threads(version)
                times[f"{version_str}"] = tms
                save_res(version, times)

        versions[version][2] = True
        with open("./versions.json", "w") as f:
            versions_json = json.dumps(versions, indent=4)
            f.write(versions_json)


def analyse_single_thread():
    path = './pyperf_res/'
    files_to_process = []
    for file_name in os.listdir(path):
        if file_name.endswith('.json'):
            files_to_process.append(file_name)

    processed_files = {}
    for file in files_to_process:
        f = open(path + file)
        data = json.load(f)
        benchmarks = {}
        for d in data['benchmarks'][1:]:
            benchmarks[d['metadata']['name']] = d['runs'][1:]
        for key, val in benchmarks.items():
            for v in val:
                v.pop('warmups')
        processed_files[f"{file.replace('.json', '')}_processed.json"] = benchmarks

    columns = {
        'py310_processed.json': '3.10.13',
        'py311_processed.json': '3.11.8',
        'py312_processed.json': '3.12.2',
        'py3120_processed.json': '3.12.0',
        'py39_processed.json': '3.9.18',
        'py3910_processed.json': '3.9.10',
        'pynogil_processed.json': 'nogil-3.9.10'
    }

    # Get complete list of benchmarks
    benchmarks = []
    for file in sorted(processed_files):
        benchmarks.extend(processed_files[file].keys())

    benchmarks = sorted(list(set(benchmarks)))
    df = {}
    df['Benchmarks'] = benchmarks
    for file in sorted(processed_files):
        all_times = []
        data = processed_files[file]
        for key in benchmarks:
            if data.get(key):
                bench = data[key]
                times = []
                for run in bench:
                    vals = run['values']
                    times.extend(vals)
                # print(times)
                avg_time = np.average(times)
                all_times.append(round(avg_time, 5))
            else:
                all_times.append(np.nan)
        df[columns[file].replace('.json', '')] = all_times

    times_df = pd.DataFrame(df)
    columns = ['Benchmarks', '3.9.10', 'nogil-3.9.10', '3.9.18', '3.10.13', '3.11.8', '3.12.0', '3.12.2']
    times_df = times_df[columns]
    times_df_notnull = times_df.dropna()
    times_df_notnull.reset_index(inplace=True, drop=True)
    times_df = times_df_notnull

    times = []
    for col in times_df.columns[1:]:
        avg_time = np.average(times_df[col])
        times.append(avg_time)

    plt.figure(figsize=(10, 7))
    labels = list(times_df.columns)[1:]

    colors = ["#ff1500", "#ff9602", "#f5cc02", "#00d200", "#00c3ff", "#0022ff", "#b700ff"]
    colors.reverse()
    for i in range(len(labels)):
        plt.bar(i, times[i], color=colors.pop())
    plt.xlabel("Python Versions")
    plt.ylabel("Avg Execution Time")
    plt.legend(labels)
    ticks = [i for i in range(len(times))]
    plt.xticks(ticks, labels=labels)
    plt.savefig(f"./images/confronto_single_thread.png", bbox_inches='tight', transparent=False, pad_inches=0.1)


def analyse_memory_single_thread():
    path = './pyperf_res/memory'
    files_to_process = []
    for file_name in os.listdir(path):
        if file_name.endswith('.json'):
            files_to_process.append(file_name)

    processed_files = {}
    for file in files_to_process:
        f = open(path + file)
        data = json.load(f)
        benchmarks = {}
        for d in data['benchmarks'][1:]:
            benchmarks[d['metadata']['name']] = d['runs'][1:]
        processed_files[f"{file.replace('.json', '')}_processed.json"] = benchmarks

    columns = {
        'py310_processed.json': '3.10.13',
        'py311_processed.json': '3.11.8',
        'py312_processed.json': '3.12.2',
        'py3120_processed.json': '3.12.0',
        'py39_processed.json': '3.9.18',
        'py3910_processed.json': '3.9.10',
        'pynogil_processed.json': 'nogil-3.9.10'
    }

    # Get complete list of benchmarks
    benchmarks = []
    for file in sorted(processed_files):
        benchmarks.extend(processed_files[file].keys())

    benchmarks = sorted(list(set(benchmarks)))
    df = {}
    df['Benchmarks'] = benchmarks
    for file in sorted(processed_files):
        all_mems = []
        data = processed_files[file]
        for key in benchmarks:
            if data.get(key):
                bench = data[key]
                mems = []
                for run in bench:
                    vals = run['values']
                    mems.extend(vals)
                # print(times)
                avg_mem = np.average(mems)
                avg_mem = avg_mem/1024/1024
                all_mems.append(round(avg_mem, 1))
            else:
                all_mems.append(np.nan)
        df[columns[file].replace('.json', '')] = all_mems
        
    mems_df = pd.DataFrame(df)
    columns = ['Benchmarks', '3.9.10', 'nogil-3.9.10', '3.9.18', '3.10.13', '3.11.8', '3.12.0', '3.12.2']
    mems_df = mems_df[columns]
    mems_df_notnull = mems_df.dropna()
    mems_df_notnull.reset_index(inplace=True, drop=True)
    mems_df = mems_df_notnull

    mems = []
    for col in mems_df.columns[1:]:
        avg_mem = np.average(mems_df[col])
        mems.append(avg_mem)

    plt.figure(figsize=(10, 7))
    labels = list(mems_df.columns)[1:]

    colors = ["#ff1500", "#ff9602", "#f5cc02", "#00d200", "#00c3ff", "#0022ff", "#b700ff"]
    colors.reverse()
    for i in range(len(labels)):
        plt.bar(i, mems[i], color=colors.pop())
    plt.xlabel("Python Versions")
    plt.ylabel("Avg Execution Time")
    plt.legend(labels)
    ticks = [i for i in range(len(mems))]
    plt.xticks(ticks, labels=labels)
    plt.savefig(f"./images/confronto_single_thread_memoria.png", bbox_inches='tight', transparent=False, pad_inches=0.1)

def analyse_multi_thread():
    arr = np.genfromtxt('times.csv',delimiter=',',dtype=str)
    df = pd.DataFrame(arr.T)
    new_header = df.iloc[0]  # grab the first row for the header
    df = df[1:]  # take the data less the header row
    df.columns = new_header  # set the header row as the df header

    plt.figure(figsize=(7, 7))
    columns = list(df.columns)
    for col in range(len(columns)):
        val = columns[col].replace("_0", "_active").replace("_1", "_notactive")
        columns[col] = val

    colors = ["#ff1500", "#ff9602", "#f5cc02", "#00d200", "#00c3ff", "#0022ff", "#b700ff"]
    colors.reverse()

    for col in df.columns:
        vals = list(df[col].astype(float))
        plt.plot(list(range(1, 51)), vals, color=colors.pop())
    plt.axvline(x=multiprocessing.cpu_count(), color=colors.pop(), linestyle='--')
    plt.xlabel("Number of threads")
    plt.ylabel("Execution time in seconds")
    legend = columns.copy()
    legend.append("Number of cores")
    plt.legend(legend)
    plt.xlim((0, 51))
    ticks = [i for i in range(51) if i % 10 == 0]
    ticks.append(multiprocessing.cpu_count())
    ticks.sort()
    plt.xticks(ticks)
    plt.savefig("./images/confronto_multi_thread.png", bbox_inches='tight', transparent=False, pad_inches=0.1)


def main():
    versions = {
        "3.9.10": [False, False, False],
        "nogil-3.9.10-1": [False, False, False],
        "3.9.18": [False, False, False],
        "3.10.13": [False, False, False],
        "3.11.8": [False, False, False],
        "3.12.2": [False, False, False],
    }

    if not os.path.exists("./images"):
        os.makedirs("./images")

    if not os.path.exists("./pyperf_res"):
        os.makedirs("./pyperf_res")

    check_file(versions)
    check_versions(versions)

    #single_thread(versions)
    memory_single_thread(versions)
    #multi_thread(versions)
    #analyse_single_thread()
    #analyse_memory_single_thread()
    #analyse_multi_thread()

if __name__ == '__main__':
    main()
