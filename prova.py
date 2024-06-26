versions = ["3.9.10", "nogil-3.9.10-1_0", "nogil-3.9.10-1_1", "3.9.18", "3.10.13", "3.11.8", "3.12.2"]
tests_dict = {"single_thread": False, "single_thread_memory": False, "multi_thread": False}
temp = dict()
for vers in versions:
    temp[vers] = tests_dict.copy()
    for test in ["single_thread", "single_thread_memory", "multi_thread"]:
        temp[vers][test] = False

versions = temp