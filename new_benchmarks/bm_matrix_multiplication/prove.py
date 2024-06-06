# import threading
# import time
# import random
# import cProfile
#
# def multiply_row(a, b, row_index, result):
#     # Compute the row result
#     num_columns_B = len(b[0])
#     num_columns_A = len(a[0])
#     for j in range(num_columns_B):
#         sum = 0
#         for k in range(num_columns_A):
#             sum += a[row_index][k] * b[k][j]
#         result[row_index][j] = sum
#
#
# def parallel_matrix_multiplication(a, b, result, row_indices):
#     for row_index in row_indices:
#         multiply_row(a, b, row_index, result)
#
#
# def multi_threaded_matrix_multiplication(a, b, num_threads):
#     num_rows = len(a)
#     result = [[0] * len(b[0]) for _ in range(num_rows)]
#     row_chunk = num_rows // num_threads
#
#     threads = []
#     for i in range(num_threads):
#         start_row = i * row_chunk
#         end_row = (i + 1) * row_chunk if i != num_threads - 1 else num_rows
#         thread = threading.Thread(target=parallel_matrix_multiplication, args=(a, b, result, range(start_row, end_row)))
#         threads.append(thread)
#         thread.start()
#
#     for thread in threads:
#         thread.join()
#
#     return result
#
#
# # Helper function to create a random matrix
# def create_random_matrix(rows, cols):
#     return [[random.random() for _ in range(cols)] for _ in range(rows)]
#
#
# def main():
#     size = 160  # Define matrix size
#     a = create_random_matrix(size, size)
#     b = create_random_matrix(size, size)
#     num_threads = 1  # Define number of threads
#
#     p = cProfile.Profile()
#     p.runcall(multiply_row(a,b,0,[]))
#     p.print_stats()
#
#     start = time.perf_counter()
#     result = multi_threaded_matrix_multiplication(a, b, num_threads)
#
#     print("Matrix multiplication completed. Time: ", time.perf_counter() - start)
#
#
# if __name__ == "__main__":
#     main()
import time

start = time.perf_counter()
a = []
for j in range(200):
    sum = 0
    for k in range(200):
        sum += A[row_index][k] * B[k][j]
    local_result[row_index][j] = sum
print("Explicit loop done. Time: ", time.perf_counter() - start)

start = time.perf_counter()
for j in range(len(b[0])):
    result[row_index][j] = sum(a[row_index][k] * b[k][j] for k in range(len(b)))
print("Generator loop done. Time: ", time.perf_counter() - start)