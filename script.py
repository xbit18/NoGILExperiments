#!/usr/bin/env python3
import asyncio
# Setup steps
# Importa librerie
import multiprocessing
import sys
from dotenv import load_dotenv
import os
import platform
import csv
import pandas as pd
import numpy as np
import json
from pprint import pprint
import matplotlib.pyplot as plt
import subprocess
import argparse
import telegram_send as tel
from datetime import datetime
from pathlib import Path


debug = False
verbose = False
capture_output=False
restart = False
telegram = False
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
    if restart:
        print("Starting over. Dumping versions.json file.")
        with open(f"./versions.json","w") as f:
            versions_json = json.dumps(versions, indent=4)
            new_versions = versions
            f.write(versions_json)
        return versions
    
    print("Checking if versions.json file exists")
    if os.path.exists(f"./versions.json"):
        with open(f"./versions.json","r") as f:
            new_versions = json.load(f)
            print("File exists - Loaded")
            
            for version, done in new_versions.items():
                for key,val in done.items():
                    if val == False:
                        return new_versions
            
            with open(f"./versions.json","w") as f:
                versions_json = json.dumps(versions, indent=4)
                new_versions = versions
                f.write(versions_json)
            #pp(versions)
    else:
        with open(f"./versions.json","w") as f:
            versions_json = json.dumps(versions, indent=4)
            new_versions = versions
            f.write(versions_json)
            print("File does not exist - Dumped")
    return new_versions

def send_message(message):
    if telegram:
        send = tel.send(messages=[message], parse_mode="Markdown",
                        disable_web_page_preview=True, conf=f'./telegram.conf')
        asyncio.run(send)

# Metodo che controlla che ogni versione specificata sia installata sul sistema.
# Se non lo è la installa, e se il processo di installazione fallisce skippa
# quella versione rimuovendola dall'elenco di versioni da testare.
def check_versions(versions):
    message=f"Checking all versions are installed along with required packages"
    send_message(message)
    print(message)

    temp = versions.copy()
    for version in temp.keys():
        version = version.replace("nogil-3.9.10-1_0","nogil-3.9.10-1").replace("nogil-3.9.10-1_1","nogil-3.9.10-1")
        if not os.path.exists(f"{os.getenv('HOME')}/.pyenv/versions/{version}"):
            print(f"Version {version} not installed. Skipping...")
            del versions[version]
            continue
            #res1 = subprocess.run(f"env PYTHON_CONFIGURE_OPTS='--enable-optimizations --with-lto' pyenv install {version}", shell=True, capture_output = capture_output)
        
        print(f"Version {version} installed")
        
    return versions

def save_res(version, times, memories, path):
    
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

    with open(f"./versions.json", "w") as f:
        versions_json = json.dumps(versions, indent=4)
        f.write(versions_json)

def exec_threads(version, THREADS, LOOPS_PER_THREAD, path):
    times = []
    memories = []
    malloc_path = path + f"/{version}_malloc"
    for idx, thread in enumerate(THREADS):
        message = "Threads: " + str(thread)
        print(message)
        send_message(message)
        
        all_time=0
        all_memory=0
        for i in range(LOOPS_PER_THREAD):
            command = f"~/.pyenv/versions/{version}/bin/python3 fib.py {thread}"
            if idx == len(THREADS)-1:
                command += f" {malloc_path}"
            command = command.replace("nogil-3.9.10-1_0","nogil-3.9.10-1").replace("nogil-3.9.10-1_1","nogil-3.9.10-1")
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
        Path(path).mkdir(parents=True, exist_ok=True)

        message=f"Starting single thread analysis..."
        send_message(message)
        print(message)

        if os.getenv('IS_HOST_MACOS') == '0':
            print("\nTuning system...")
            subprocess.run(f"pyperf system tune", shell=True, capture_output = capture_output)

        for version, done in versions.items():
            if done['single_thread']:
                continue
            
            message=f"Single thread analysis for {version} started"
            send_message(message)
            print(message)
            
            version_str = version.replace("nogil-3.9.10-1_0","nogil-3.9.10-1").replace("nogil-3.9.10-1_1","nogil-3.9.10-1")
            output_path = f"{path}/{version}.json"
            command = f"pyperformance run --python={os.getenv('HOME')}/.pyenv/versions/{version_str}/bin/python -o {output_path}"
            
            if debug:
                command += " --benchmarks=2to3"

            if version == "nogil-3.9.10-1_0":
                os.environ["PYTHONGIL"] = "0"
                command += " --inherit-environ=PYTHONGIL"
            
            if version == "nogil-3.9.10-1_1":
                os.environ["PYTHONGIL"] = "1"
                command += " --inherit-environ=PYTHONGIL"
            
            print("Running command: ", command, "\n")
            
            if debug:
                continue
            
            subprocess.run(
                command,
                shell=True, capture_output = capture_output)

            print("Done")
            send_message(f"Done")

            versions[version]['single_thread'] = True
            update_versions(versions)

        message=f"Single thread analysis done"
        send_message(message)
        print(message+"\n")

        if os.getenv('IS_HOST_MACOS') == '0':
            print("Resetting system...\n")
            subprocess.run("pyperf system reset", shell=True, capture_output = capture_output)
    except Exception as e:
        print(e)

# Test multi thread
# Variabili per definire quanti thread e quanti loop per thread
def multi_thread(versions):
    global date_time_str, debug, THREADS, results_path
    path=f"{results_path}{date_time_str}/multi_thread"
    Path(path).mkdir(parents=True, exist_ok=True)

    print("\nStarting multi thread analysis...")
    if os.environ.get('THREADS') is None:
        print("\nTHREADS NUMBER NOT SPECIFIED\nAborting...")
        return 
    
    if os.environ.get('ITERS') is None:
        print("\nITERS NUMBER NOT SPECIFIED\nAborting...")
        return 

    LOOPS_PER_THREAD = int(os.getenv('ITERS'))

    times = {}
    memories = {}
    for version, done in versions.items():
        
        if done['multi_thread']:
            continue
        
        message=f"Multi thread analysis for {version} started"
        send_message(message)
        print(message)
        #send_message(f"Multi thread analysis for {version} started")
        # Se non è nogil calcola i tempi normalmente
        if version == "nogil-3.9.10-1_0":
            os.environ["PYTHONGIL"] = '0'
        
        if version == "nogil-3.9.10-1_1":
            os.environ["PYTHONGIL"] = '1'

        res_time, res_mem = exec_threads(version, THREADS, LOOPS_PER_THREAD, path)
        times[f"{version}"] = res_time
        memories[f"{version}"] = res_mem
        save_res(version, times, memories, path)
        
        #send_message(f"Done")

        versions[version]['multi_thread'] = True
        update_versions(versions)
        print("\n")
    
    message=f"Multi thread analysis done."
    send_message(message)
    print(message)

# Test memoria multi thread
def memory_single_thread(versions):
    global date_time_str, debug, results_path
    path=f"{results_path}{date_time_str}/memory_single_thread"
    Path(path).mkdir(parents=True, exist_ok=True)

    message=f"Starting single thread memory analysis..."
    send_message(message)
    print(message)

    if os.getenv('IS_HOST_MACOS') == '0':
        print("Tuning system...")
        subprocess.run(f"pyperf system tune", shell=True, capture_output = capture_output)

    for version, done in versions.items():
        if done['single_thread_memory']:
            continue
        
        message = f"Single thread memory analysis for {version} started"
        send_message(message)
        print(message)
        
        version_str = version.replace("nogil-3.9.10-1_0","nogil-3.9.10-1").replace("nogil-3.9.10-1_1","nogil-3.9.10-1")
        output_path = f"{path}/{version}.json"
        command = f"{os.getenv('HOME')}/.pyenv/versions/{version_str}/bin/python -m pyperformance run -m -o {output_path}"
        
        if not debug and "nogil-3.9.10-1" in version:
            command += " --benchmarks=-gc_traversal"

        if debug:
            command += " --benchmarks=2to3"

        if version == "nogil-3.9.10-1_0":
                os.environ["PYTHONGIL"] = "0"
                command += " --inherit-environ=PYTHONGIL"
            
        if version == "nogil-3.9.10-1_1":
            os.environ["PYTHONGIL"] = "1"
            command += " --inherit-environ=PYTHONGIL"
        
        print("Running command: ", command, "\n")

        if debug:
            continue

        subprocess.run(
            command,
            shell=True, capture_output = capture_output)

        send_message(f"Done")

        versions[version]['single_thread_memory'] = True
        update_versions(versions)

    message = f"Single thread memory analysis done"
    send_message(message)
    print(message+"\n")
    
    if os.getenv('IS_HOST_MACOS') == '0':
        print("Resetting system...\n")
        subprocess.run(f"pyperf system reset", shell=True, capture_output = capture_output)


def main():
    global debug, verbose, THREADS, capture_output, restart, telegram

    dotenv_path = Path('./.env')
    load_dotenv(dotenv_path=dotenv_path)

    print("Starting up...")
    try:
        if os.getenv('DEBUG') is not None: debug=bool(int(os.getenv('DEBUG')))
        if os.getenv('VERBOSE') is not None: verbose=bool(int(os.getenv('VERBOSE')))
        if os.getenv('RESTART') is not None: restart=bool(int(os.getenv('RESTART')))
        if os.getenv('TELEGRAM') is not None: telegram=bool(int(os.getenv('TELEGRAM')))
    except TypeError as e:
        pass

    print("Run parameters:")
    print(f"DEBUG: {debug}")
    print(f"VERBOSE: {verbose}")
    print(f"RESTART: {restart}")
    print(f"TELEGRAM: {telegram}\n")

    capture_output = not verbose
    send_message('#' * 20)
    versions = {
        "3.9.10": {
            "single_thread": False,
            "single_thread_memory": False,
            "multi_thread": False
        },
        "nogil-3.9.10-1_0": {
            "single_thread": False,
            "single_thread_memory": False,
            "multi_thread": False
        },
        "nogil-3.9.10-1_1": {
            "single_thread": False,
            "single_thread_memory": False,
            "multi_thread": False
        },
        "3.9.18": {
            "single_thread": False,
            "single_thread_memory": False,
            "multi_thread": False
        },
        "3.10.13": {
            "single_thread": False,
            "single_thread_memory": False,
            "multi_thread": False
        },
        "3.11.8": {
            "single_thread": False,
            "single_thread_memory": False,
            "multi_thread": False
        },
        "3.12.2": {
            "single_thread": False,
            "single_thread_memory": False,
            "multi_thread": False
        }
    }

    #Path(f"{os.getenv('HOME')}/NoGILExperiments/images").mkdir(parents=True, exist_ok=True)
    #Path(f"{os.getenv('HOME')}/NoGILExperiments/images/{date_time_str}").mkdir(parents=True, exist_ok=True)

    MAX_THREADS = int(os.getenv('THREADS'))

    THREADS=[]
    i=0
    while 2**i <= MAX_THREADS:
        THREADS.append(2**i)
        i+=1

    versions = check_file(versions)
    versions = check_versions(versions)
    
    single_thread(versions)
    memory_single_thread(versions)
    multi_thread(versions)

if __name__ == '__main__':
    main()
