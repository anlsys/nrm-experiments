/*
 * =====================================================================================
 *
 *       Filename:  gpu.h
 *
 *    Description:  Get GPU elements
 *
 *        Version:  1.0
 *        Created:  21/10/2021 21:54:17
 *       Revision:  none
 *       Compiler:  gcc
 *
 *         Author:  Idriss Daoudi
 *   Organization:  Argonne National Laboratory
 *
 * =====================================================================================
 */

int get_gpus (struct device** devices, hwloc_topology_t topology, hwloc_obj_t object, int index)
{
    char type[STR_SIZE];
    
    while ((object = hwloc_get_next_osdev(topology, object)) != NULL)
    {
        devices[index] = malloc(sizeof(struct device));
        
        int i = 0;
        int id = 0;
        const char* size;
        
        hwloc_obj_type_snprintf(type, sizeof(type), object, 0);
        const char* model = hwloc_obj_get_info_by_name(object, "GPUModel");
        const char* backend = hwloc_obj_get_info_by_name(object,"Backend");
        int amount = hwloc_get_nbobjs_by_type(topology, HWLOC_OBJ_OS_DEVICE);
        
        strcpy(devices[index]->type, type);
        strcpy(devices[index]->name, object->name);
        strcpy(devices[index]->model, model);
        strcpy(devices[index]->backend, backend);
        
        if ((sscanf(object->name, "cuda%d", &id) == 1)
            || (sscanf(object->name, "rsmi%d", &id) == 1)
            || (sscanf(object->name, "nvml%d", &id) == 1))
        {
            size = hwloc_obj_get_info_by_name(object,"CUDAGlobalMemorySize");
            devices[index]->id = id;
        }
        else if (sscanf(object->name, "opencl%dd%d", &i, &id) == 2)
        {
            size = hwloc_obj_get_info_by_name(object,"OpenCLGlobalMemorySize");
            devices[index]->id = id;
        }
        devices[index]->size = atoi(size);
        devices[index]->amount = amount;
        
        index++;
    }
    return index;
}
