# import time
# import random
# from concurrent.futures import ThreadPoolExecutor
#
# def multiply_row(A, B, row_index, local_result):
#     num_columns_B = len(B[0])
#     num_columns_A = len(A[0])
#     for j in range(num_columns_B):
#         sum = 0
#         for k in range(num_columns_A):
#             sum += A[row_index][k] * B[k][j]
#         local_result[row_index][j] = sum
#
# def parallel_matrix_multiplication(a, b, start_row, end_row):
#     local_result = [[0] * len(b[0]) for _ in range(len(a))]
#
#     for row_index in range(start_row, end_row):
#         multiply_row(a, b, row_index, local_result)
#
#     return local_result
#
# def multi_threaded_matrix_multiplication(a, b, num_threads):
#     num_rows = len(a)
#     result = []
#     for _ in range(num_rows):
#         result.append([0] * len(b[0]))
#     row_chunk = num_rows // num_threads
#
#     futures = []
#     with ThreadPoolExecutor(max_workers=num_threads) as executor:
#         for i in range(num_threads):
#             start_row = i * row_chunk
#             end_row = (i + 1) * row_chunk if i != num_threads - 1 else num_rows
#             future = executor.submit(parallel_matrix_multiplication, a.copy(), b.copy(), start_row, end_row)
#             futures.append(future)
#
#     results = [future.result() for future in futures]
#
#     # Combine local results into the final result matrix
#     for local_result in results:
#         for i in range(num_rows):
#             for j in range(len(b[0])):
#                 result[i][j] += local_result[i][j]
#
#     return result
#
# # Helper function to create a random matrix
# def create_random_matrix(rows, cols):
#     return [[random.random() for _ in range(cols)] for _ in range(rows)]
#
# def main():
#     size = 1000  # Define matrix size
#
#     a = create_random_matrix(size, size)
#     b = create_random_matrix(size, size)
#
#     num_threads = 8 # Define number of threads
#
#     start = time.perf_counter()
#
#     result = multi_threaded_matrix_multiplication(a, b, num_threads)
#     print("Matrix multiplication completed.", time.perf_counter() - start, "seconds.")
#
# if __name__ == "__main__":
#     main()

import threading
import time
import random


def copy_row(row):
    return [float(value + 0.0) for value in row]


def copy_matrix(matrix):
    return [copy_row(row) for row in matrix]


def multiply_row(A, B, row_index, result):
    # Compute the row result
    num_columns_B = len(B[0])
    num_columns_A = len(A[0])
    for j in range(num_columns_B):
        sum = 0
        for k in range(num_columns_A):
            sum += A[row_index][k] * B[k][j]
        result.append(sum)


def parallel_matrix_multiplication(a, b, result, row_indices):
    a = copy_matrix(a)
    b = copy_matrix(b)
    for row_index in row_indices:
        tmp_result = []
        multiply_row(a, b, row_index, tmp_result)
        result[row_index] = tmp_result


def multi_threaded_matrix_multiplication(a, b, num_threads):
    num_rows = len(a)
    result = [[0] * len(b[0]) for _ in range(num_rows)]
    row_chunk = num_rows // num_threads

    threads = []
    for i in range(num_threads):
        start_row = i * row_chunk
        end_row = (i + 1) * row_chunk if i != num_threads - 1 else num_rows
        thread = threading.Thread(target=parallel_matrix_multiplication, args=(a, b, result, range(start_row, end_row)))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    return result


# Helper function to create a random matrix
def create_random_matrix(rows, cols):
    return [[random.random() for _ in range(cols)] for _ in range(rows)]


def main():
    size = 1000  # Define matrix size
    a = create_random_matrix(size, size)
    b = create_random_matrix(size, size)
    num_threads = 8  # Define number of threads

    start = time.perf_counter()

    result = multi_threaded_matrix_multiplication(a, b, num_threads)
    print("Matrix multiplication completed.", time.perf_counter() - start, "seconds.")


if __name__ == "__main__":
    main()