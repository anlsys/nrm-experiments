from libc.stdlib cimport malloc, free
from libc.stdio cimport printf
from cython.parallel import prange, parallel
cimport cython.parallel
cimport openmp
import time

def scale(long size):
        cdef int *a = <int*> malloc(size * sizeof(int))
        cdef int *b = <int*> malloc(size * sizeof(int))
        cdef int scalar = 3
        cdef int num_threads
        cdef int MAX_ITER = 1000
        cdef int i, it

        for i in prange(1, nogil=True):
            num_threads = openmp.omp_get_num_threads()

        for i in range(size):
            a[i] = 1
            b[i] = 1

        start = int(round(time.time() * 1000))
        for it in range(MAX_ITER):
            for i in prange(size, nogil=True):
                b[i] = scalar * a[i]
        end = int(round(time.time() * 1000))

        res = (end-start)/MAX_ITER
        size = (size*8)/1000000
        assert(b[0] == 3)
        print("########################################")
        print("######### Python STREAM Scale ##########")
        print("########################################")
        print("Number of threads:"), num_threads
        print("Size: " + str(size) + " Mb")
        print("Time: " + str(res) + "ms")
        free(a)
        free(b)
