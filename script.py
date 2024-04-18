#!/usr/bin/env python3
import asyncio
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
import argparse
import telegram_send as tel
from datetime import datetime
from pathlib import Path


debug = False
date_time_str = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
results_path = "./pyperf_res/"
THREADS = []

class SmartFormatter(argparse.HelpFormatter):
    """
    Class that implements a better formatter for the command line help text
    """

    def _split_lines(self, text, width):
        """
        Makes sure that every help string that starts with
        'R|' is formatted so that '\n' is properly rendered
        as a new line
        """
        if text.startswith('R|'):
            return text[2:].splitlines()
        return argparse.HelpFormatter._split_lines(self, text, width)

def check_file(versions):
    print("Checking if versions.json file exists")
    if os.path.exists(f"{os.environ['HOME']}/NoGILExperiments/versions.json"):
        with open(f"{os.environ['HOME']}/NoGILExperiments/versions.json","r") as f:
            new_versions = json.load(f)
            print("File exists - Loaded")
            #pp(versions)
    else:
        with open(f"{os.environ['HOME']}/NoGILExperiments/versions.json","w") as f:
            versions_json = json.dumps(versions, indent=4)
            new_versions = versions
            f.write(versions_json)
            print("File does not exist - Dumped")
    return new_versions

def send_message(message):
    send = tel.send(messages=[message], parse_mode="Markdown",
                    disable_web_page_preview=True, conf=f'{os.environ['HOME']}/NoGILExperiments/telegram.conf')
    asyncio.run(send)

# Metodo che controlla che ogni versione specificata sia installata sul sistema.
# Se non lo è la installa, e se il processo di installazione fallisce skippa
# quella versione rimuovendola dall'elenco di versioni da testare.
def check_versions(versions):
    print("Checking all versions are installed along with required packages")
    temp = versions.copy()
    for version in temp.keys():

        if not os.path.exists(f"{os.environ['HOME']}/.pyenv/versions/{version}"):
            del versions[version]
            continue
            #res1 = subprocess.run(f"env PYTHON_CONFIGURE_OPTS='--enable-optimizations --with-lto' pyenv install {version}", shell=True)
        
        checking_pyperformance = subprocess.run(f"{os.environ['HOME']}/.pyenv/versions/{version}/bin/python -m pip list | grep 'pyperformance'", shell=True, capture_output=True)
        if checking_pyperformance.returncode == 1:
            res2 = subprocess.run(f"{os.environ['HOME']}/.pyenv/versions/{version}/bin/python -m pip install pyperformance", shell=True, capture_output=True)
        
        checking_telegram_send = subprocess.run(f"{os.environ['HOME']}/.pyenv/versions/{version}/bin/python -m pip list | grep 'telegram_send'", shell=True, capture_output=True)
        if checking_telegram_send.returncode == 1:
            res3 = subprocess.run(f"{os.environ['HOME']}/.pyenv/versions/{version}/bin/python -m pip install telegram_send",
                                shell=True, capture_output=True)
    return versions

def save_res(version, times, memories, path):
    global debug
    if debug:
        return
    
    if times != {} and times is not None:
        with open(f"{path}/times.csv", "a") as csv_file:
                writer = csv.writer(csv_file, delimiter=',')
                to_insert = []
                to_insert.append(version)
                to_insert.extend(times[version])
                writer.writerow(to_insert)

    if memories != {} and times is not None:
        with open(f"{path}/memories.csv", "a") as csv_file:
                writer = csv.writer(csv_file, delimiter=',')
                to_insert = []
                to_insert.append(version)
                to_insert.extend(memories[version])
                writer.writerow(to_insert)

def update_versions(versions):
    global debug
    if debug:
        return

    with open(f"{os.environ['HOME']}/NoGILExperiments/versions.json", "w") as f:
        versions_json = json.dumps(versions, indent=4)
        f.write(versions_json)

def exec_threads(version, THREADS, LOOPS_PER_THREAD, path):
    times = []
    memories = []
    malloc_path = path + f"/{version}_malloc"
    for idx, thread in enumerate(THREADS):
        print("Threads:", thread)
        all_time=0
        all_memory=0
        for i in range(LOOPS_PER_THREAD):
            command = f"~/.pyenv/versions/{version}/bin/python3 fib.py {thread}"
            if idx == len(THREADS)-1:
                command += f" {malloc_path}"
            try:
            	output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
            except  subprocess.CalledProcessError as e:
		print(e.cmd, e.returncode, e.output)
		quit()
            time, mem = output.decode(sys.stdout.encoding).replace('\n','').split(" ")
            all_time += float(time)
            all_memory += int(mem)
        times.append(round(all_time/LOOPS_PER_THREAD, ndigits=3))
        memories.append(round(all_memory/LOOPS_PER_THREAD, ndigits=3))
    return times, memories

# Test single thread
def single_thread(versions):
    try:
        global date_time_str, debug, results_path
        path=f"{results_path}{date_time_str}/single_thread"
        if debug:
            print(path)
            return
        Path(path).mkdir(parents=True, exist_ok=True)

        print("\nStarting single thread analysis...")
        print("\nTuning system...")
        subprocess.run(f"pyperf system tune", shell=True)

        for version, done in versions.items():
            if done[0]:
                continue
            
            send_message(f"Single thread analyis for {version} started")
            
            command = f"pyperformance run --python={os.environ['HOME']}/.pyenv/versions/{version}/bin/python -o {path}/{version}.json --benchmarks=2to3"
            subprocess.run(
                command,
                shell=True)

            send_message(f"Done")

            versions[version][0] = True
            with open(f"{os.environ['HOME']}/NoGILExperiments/versions.json", "w") as f:
                versions_json = json.dumps(versions, indent=4)
                f.write(versions_json)

        print("\nSingle thread analysis done. Resetting system...")
        subprocess.run("pyperf system reset", shell=True)
    except Exception as e:
        print(e)

# Test multi thread
# Variabili per definire quanti thread e quanti loop per thread
def multi_thread(versions):
    global date_time_str, debug, THREADS, results_path
    path=f"{results_path}{date_time_str}/multi_thread"
    if debug:
        print(path)
        return
    Path(path).mkdir(parents=True, exist_ok=True)

    print("\nStarting multi thread analysis...")
    if os.environ.get('THREADS') is None:
        print("\nTHREADS NUMBER NOT SPECIFIED\nAborting...")
        return 
    
    if os.environ.get('ITERS') is None:
        print("\nITERS NUMBER NOT SPECIFIED\nAborting...")
        return 

    LOOPS_PER_THREAD = int(os.environ['ITERS'])

    times = {}
    memories = {}
    for version, done in versions.items():
        
        if done[2]:
            continue
        
        print(f"\nCurrent version: {version}")
        #send_message(f"Multi thread analyis for {version} started")
        # Se non è nogil calcola i tempi normalmente
        if version != "nogil-3.9.10-1":
            res_time, res_mem = exec_threads(version, THREADS, LOOPS_PER_THREAD, path)
            times[f"{version}"] = res_time
            memories[f"{version}"] = res_mem
            save_res(version, times, memories, path)

        # Altrimenti calcolali sia con PYTHONGIL=0 che PYTHONGIL=1
        else:
            for val in [0, 1]:
                os.environ["PYTHONGIL"] = str(val)
                print(f"PYTHONGIL={os.environ.get('PYTHONGIL')}")
                version_str = f"3.9.10-nogil_{val}"
                res_time, res_mem = exec_threads(version, THREADS, LOOPS_PER_THREAD, path)
                times[f"{version_str}"] = res_time
                memories[f"{version_str}"] = res_mem
                save_res(version_str, times, memories, path)
        
        #send_message(f"Done")

        versions[version][2] = True
        update_versions(versions)
    
    print("\nMulti thread analysis done.")

# Test memoria multi thread
def memory_single_thread(versions):
    global date_time_str, debug, results_path
    path=f"{results_path}{date_time_str}/memory_single_thread"
    if debug:
        print(path)
        return
    Path(path).mkdir(parents=True, exist_ok=True)

    print("\nStarting single thread memory analysis...")
    print("\nTuning system...")
    subprocess.run(f"pyperf system tune", shell=True)

    for version, done in versions.items():
        if done[1]:
            continue
        
        send_message(f"Single thread memory analyis for {version} started")

        command = f"{os.environ['HOME']}/.pyenv/versions/{version}/bin/python -m pyperformance run -m -o {path}/{version}.json --benchmarks=2to3"
        if version == "nogil-3.9.10-1":
            command += " --benchmarks=-gc_traversal"
        
        subprocess.run(
            command,
            shell=True)

        send_message(f"Done")

        versions[version][1] = True
        update_versions(versions)

    print("\nSingle thread memory analysis done. Resetting system...")
    subprocess.run(f"pyperf system reset", shell=True)



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
    global debug, THREADS

    print("Starting up...")

    parser = argparse.ArgumentParser(description='',
                                     prog="",
                                     formatter_class=SmartFormatter)

    parser.add_argument('-d', '--debug', 
                        default=False,
                        const=True,
                        action='store_const',
                        help="Debug Mode ON. When on the script won't save results.")
                             
    args = parser.parse_args()

    debug=args.debug

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
    if not os.path.exists(f"{os.environ['HOME']}/NoGILExperiments/pyperf_res"):
        os.makedirs(f"{os.environ['HOME']}/NoGILExperiments/pyperf_res")

    MAX_THREADS = int(os.environ['THREADS'])
    
    THREADS=[]
    i=0
    while 2**i <= MAX_THREADS:
        THREADS.append(2**i)
        i+=1

    versions = check_file(versions)
    versions = check_versions(versions)
    
    #single_thread(versions)
    #memory_single_thread(versions)
    multi_thread(versions)

    #analyse_single_thread()
    #analyse_memory_single_thread()
    #analyse_multi_thread()

if __name__ == '__main__':
    main()
