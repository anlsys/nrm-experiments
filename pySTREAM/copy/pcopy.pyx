from libc.stdlib cimport malloc, free
from libc.stdio cimport printf
from cython.parallel import prange, parallel
cimport cython.parallel
cimport openmp
import time
import sys 
import os

sys.path.append(os.path.realpath("../../../nrm-python/nrm"))
from progress import Progress

def pcopy(long size):
        cdef int *a = <int*> malloc(size * sizeof(int))
        cdef int *b = <int*> malloc(size * sizeof(int))
        cdef int num_threads
        cdef int MAX_ITER = 1000
        cdef int i, it

        prog = Progress()
        prog.setup()
        
        for i in prange(1, nogil=True):
            num_threads = openmp.omp_get_num_threads()

        for i in range(size):
            a[i] = 1
            b[i] = 2

        start = int(round(time.time() * 1000))
        for it in range(MAX_ITER):
            for i in prange(size, nogil=True):
                b[i] = a[i]
            prog.progress_report(1)
        end = int(round(time.time() * 1000))

        prog.shutdown()
        res = (end-start)/MAX_ITER
        size = (size*8)/1000000
        assert(b[0] == 1)
        print("########################################")
        print("########## Python STREAM Copy ##########")
        print("########################################")
        print("Number of threads:"), num_threads
        print("Size: " + str(size) + " Mb")
        print("Time: " + str(res) + "ms")
        free(a)
        free(b)
