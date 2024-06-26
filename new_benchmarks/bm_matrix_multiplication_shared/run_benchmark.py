import random
from concurrent.futures import ThreadPoolExecutor
import pyperf

def multiply_row(A, B, row_index, local_result):
    num_columns_B = len(B[0])
    num_columns_A = len(A[0])
    for j in range(num_columns_B):
        sum = 0
        for k in range(num_columns_A):
            sum += A[row_index][k] * B[k][j]
        local_result[row_index][j] = sum

def parallel_matrix_multiplication(a, b, start_row, end_row):
    local_result = [[0] * len(b[0]) for _ in range(len(a))]

    for row_index in range(start_row, end_row):
        multiply_row(a, b, row_index, local_result)

    return local_result

def multi_threaded_matrix_multiplication(a, b, num_threads):
    num_rows = len(a)
    result = []
    for _ in range(num_rows):
        result.append([0] * len(b[0]))
    row_chunk = num_rows // num_threads

    futures = []
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        for i in range(num_threads):
            start_row = i * row_chunk
            end_row = (i + 1) * row_chunk if i != num_threads - 1 else num_rows
            future = executor.submit(parallel_matrix_multiplication, a, b, start_row, end_row)
            futures.append(future)

    results = [future.result() for future in futures]

    # Combine local results into the final result matrix
    for local_result in results:
        for i in range(num_rows):
            for j in range(len(b[0])):
                result[i][j] += local_result[i][j]

    return result

# Helper function to create a random matrix
def create_random_matrix(rows, cols):
    return [[random.random() for _ in range(cols)] for _ in range(rows)]

def run_bench():
    size = 500  # Define matrix size

    a = create_random_matrix(size, size)
    b = create_random_matrix(size, size)

    num_threads = 8 # Define number of threads
    multi_threaded_matrix_multiplication(a, b, num_threads)

def main():
    runner = pyperf.Runner()
    runner.metadata['description'] = "Matrix moltiplication with shared lists"

    runner.bench_func('matrix_mult_shared', run_bench)

if __name__ == "__main__":
    main()