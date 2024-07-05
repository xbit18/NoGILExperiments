import subprocess
import time
import aiohttp.client_exceptions
import pyperf
import os
import sysconfig
import platform
import aiohttp
import asyncio
import time
import requests

# IMPORTANTE ESPORTARE PYTHON_GIL=0 PRIMA DI ESEGUIRE IL BENCHMARK E INCLUDERLO CON INHERIT_ENV

def start_flask_server():
    # Start Flask server in a subprocess
    version = platform.python_version()
    command = [f'~/.pyenv/versions/{version}/bin/python ./server.py']
    
    # print(command)
    proc = subprocess.Popen(command, cwd='new_benchmarks/bm_multiple_clients', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return proc


async def make_request(session, url):
    async with session.get(url) as response:
        result = await response.json()
        return result


async def simulate_clients():
    num_clients = 8
    url = 'http://127.0.0.1:5000/task'
    tasks = []
    try:
        async with aiohttp.ClientSession() as session:
            for _ in range(num_clients):
                task = asyncio.ensure_future(make_request(session, url))
                tasks.append(task)
            
            await asyncio.gather(*tasks)
    except aiohttp.client_exceptions.ClientConnectorError as e:
        print("Error:", e)


def run_benchmark():
    start = time.time()
    asyncio.run(simulate_clients())
    end = time.time()
    #print(f"Handled 8 requests in {end - start:.2f} seconds")

def main():
    # Start Flask server
    # Benchmark using pyperformance

    # while True:
    #     try:
    #         requests.get('http://localhost:5000/python').json()
    #     except requests.exceptions.ConnectionError:
    #         break # if server is not active start it again

    proc = start_flask_server()
    #print("Server started with PID:", proc.pid)
    #check if server has started
    while True:
        try:
            requests.get('http://localhost:5000/python')
            break
        except requests.exceptions.ConnectionError:
            pass
    
    runner = pyperf.Runner()
    runner.metadata['description'] = "Benchmarking Flask server with client requests"
    runner.bench_func('flask_server', run_benchmark)
    try:
        requests.get('http://localhost:5000/shutdown')
    except Exception:
        pass

if __name__ == '__main__':
    main()
    # while True:
    #     try:
    #         requests.get('http://localhost:5000/python').json()
    #     except requests.exceptions.ConnectionError:
    #         break # if server is not active start it again

    # proc = start_flask_server()
    # print("Server started with PID:", proc.pid)
    # #check if server has started
    # while True:
    #     try:
    #         requests.get('http://localhost:5000/python').json()
    #         break
    #     except requests.exceptions.ConnectionError:
    #         pass
    # run_benchmark()
    # requests.get('http://localhost:5000/shutdown')