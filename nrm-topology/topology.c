/*
 * =====================================================================================
 *
 *       Filename:  topology.c
 *
 *    Description:  Main file
 *
 *        Version:  1.0
 *        Created:  21/10/2021 01:47:22
 *       Revision:  none
 *       Compiler:  gcc
 *
 *         Author:  Idriss Daoudi
 *   Organization:  Argonne National Laboratory 
 *
 * =====================================================================================
 */
#include <stdlib.h>
#include <hwloc.h>

#define MAX 1000

#include "device.h"
#include "cpu.h"
#include "gpu.h"


int main ()
{
    hwloc_topology_t topology = NULL;
    hwloc_topology_init(&topology);
    // Since instruction caches, I/O and Misc objects are ignored by default
    hwloc_topology_set_io_types_filter(topology, HWLOC_TYPE_FILTER_KEEP_ALL);
    //hwloc_topology_set_io_types_filter(topology, HWLOC_TYPE_FILTER_KEEP_IMPORTANT);
    // Then, load
    hwloc_topology_load(topology);
    
    hwloc_obj_t cpu_object = NULL;
    hwloc_obj_t gpu_object = NULL;
    
    struct device **devices = NULL;
    devices = malloc(sizeof(struct device*)*MAX);
    
    int index = 0;
    index = get_cpus(devices, topology, cpu_object, index);
    printf("index after cpus: %d\n", index);
    index = get_gpus(devices, topology, gpu_object, index);
    printf("index after gpus: %d\n", index);
    
    printf("Some prints...\n");
    for (int i = 0; i < index; i++)
    {
        printf("Type: %s\n", devices[i]->type);
        printf("Name: %s\n", devices[i]->name);
        printf("Model: %s\n", devices[i]->model);
        printf("Backend: %s\n", devices[i]->backend);
        printf("MemorySize: %f\n", devices[i]->size);
        printf("Amount: %d\n", devices[i]->amount);
        printf("ID: %d\n", devices[i]->id);
        printf("\n");
    }
    free(devices);
}


