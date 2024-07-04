from flask import Flask, request, jsonify
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import platform
import os
import signal

app = Flask(__name__)

# Create a ThreadPoolExecutor with a fixed number of threads
executor = ThreadPoolExecutor(max_workers=8)

# Function to handle a long-running task
def cpu_bound_task():
    result = 0
    for i in range(0, 10000000):
        result += i * i

@app.route('/python', methods=['GET'])
def return_version():
    return jsonify({'version': platform.python_version()})

@app.route('/task', methods=['GET'])
def handle_task():
    future = executor.submit(cpu_bound_task)
    result = future.result()  # Wait for the task to complete
    return jsonify({'result': result})

@app.route('/shutdown', methods=['GET'])
def shutdown():
   print("Shutting down gracefully...")
   os.kill(os.getpid(), signal.SIGINT)
   return 'Server shutting down...'

if __name__ == '__main__':
    app.run(port=5000, debug=True)