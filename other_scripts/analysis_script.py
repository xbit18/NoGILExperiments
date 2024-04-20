import os
import json
import numpy as np
import pandas as pd
import multiprocessing
import datetime
from pathlib import Path
import matplotlib.pyplot as plt
date_time_str = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")

def analyse_single_thread():
    global results_path
    all_subdirs = [results_path+d for d in os.listdir(results_path) if os.path.isdir(results_path+d) and d!="vecchi_dati"]
    latest_subdir = max(all_subdirs, key=os.path.getmtime)

    test_path = latest_subdir + "/single_thread/"


    files_to_process = []
    for file_name in os.listdir(test_path):
        if file_name.endswith('.json'):
            files_to_process.append(file_name)

    processed_files = {}
    for file in files_to_process:
        f = open(test_path + file)
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
    plt.savefig(f"./images/{date_time_str}/confronto_single_thread.png", bbox_inches='tight', transparent=False, pad_inches=0.1)

def analyse_memory_single_thread():
    global results_path
    all_subdirs = [results_path+d for d in os.listdir(results_path) if os.path.isdir(results_path+d) and d!="vecchi_dati"]
    latest_subdir = max(all_subdirs, key=os.path.getmtime)

    test_path = latest_subdir + "/memory_single_thread/"


    files_to_process = []
    for file_name in os.listdir(test_path):
        if file_name.endswith('.json'):
            files_to_process.append(file_name)

    processed_files = {}
    for file in files_to_process:
        f = open(test_path + file)
        data = json.load(f)
        benchmarks = {}
        for d in data['benchmarks'][1:]:
            benchmarks[d['metadata']['name']] = d['runs'][1:]
        processed_files[f"{file.replace('.json', '')}_processed.json"] = benchmarks

    columns = {
        '3.10.13_processed.json': '3.10.13',
        '3.11.8_processed.json': '3.11.8',
        '3.12.2_processed.json': '3.12.2',
        '3.9.18_processed.json': '3.9.18',
        '3.9.10_processed.json': '3.9.10',
        'nogil-3.9.10-1_processed.json': 'nogil-3.9.10'
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
    columns = ['Benchmarks', '3.9.10', 'nogil-3.9.10', '3.9.18', '3.10.13', '3.11.8', '3.12.2']
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
    plt.ylabel("Avg Memory Usage (MB)")
    plt.legend(labels)
    ticks = [i for i in range(len(mems))]
    plt.xticks(ticks, labels=labels)
    plt.savefig(f"./images/{date_time_str}/confronto_single_thread_memoria.png", bbox_inches='tight', transparent=False, pad_inches=0.1)

def analyse_multi_thread():
    global results_path, THREADS
    all_subdirs = [results_path+d for d in os.listdir(results_path) if os.path.isdir(results_path+d) and d!="vecchi_dati"]
    latest_subdir = max(all_subdirs, key=os.path.getmtime)
    test_path = latest_subdir + "/multi_thread"

    arr = np.genfromtxt(f'{test_path}/memories.csv', delimiter=',',dtype=str)
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
        color = colors.pop()
        plt.plot(THREADS, vals, color=color)
        colors.insert(0,color)

    plt.xlabel("Number of threads")
    plt.ylabel("Execution memory in bytes")
    legend = columns.copy()
    plt.legend(legend)
    plt.savefig(f"./images/{date_time_str}/confronto_multi_thread_memoria.png", bbox_inches='tight', transparent=False, pad_inches=0.1)

    arr = np.genfromtxt(f'{test_path}/times.csv', delimiter=',',dtype=str)
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
        color = colors.pop()
        plt.plot(THREADS, vals, color=color)
        colors.insert(0,color)
    
    color = colors.pop()
    plt.axvline(x=multiprocessing.cpu_count(), color=color, linestyle='--')
    colors.insert(0,color)
    plt.xlabel("Number of threads")
    plt.ylabel("Execution time in seconds")
    legend = columns.copy()
    legend.append("Number of cores")
    plt.legend(legend)
    plt.xlim(THREADS[0], THREADS[-1])
    ticks = THREADS
    ticks.append(multiprocessing.cpu_count())
    ticks = list(set(ticks))
    ticks.sort()
    plt.xticks(ticks)
    plt.savefig(f"./images/{date_time_str}/confronto_multi_thread.png", bbox_inches='tight', transparent=False, pad_inches=0.1)

def main():
    
    versions = {
        #"3.9.10": [False, False, False],
        #"nogil-3.9.10-1": [False, False, False],
        #"3.9.18": [False, False, False],
        #"3.10.13": [False, False, False],
        #"3.11.8": [False, False, False],
        "3.12.2": [False, False, False],
    }

    Path(f"{os.environ['HOME']}/NoGILExperiments/images").mkdir(parents=True, exist_ok=True)
    Path(f"{os.environ['HOME']}/NoGILExperiments/images/{date_time_str}").mkdir(parents=True, exist_ok=True)

    analyse_single_thread()
    analyse_memory_single_thread()
    analyse_multi_thread()