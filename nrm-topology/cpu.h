/*
 * =====================================================================================
 *
 *       Filename:  cpu.h
 *
 *    Description:  Get CPU elements
 *
 *        Version:  1.0
 *        Created:  21/10/2021 23:04:50
 *       Revision:  none
 *       Compiler:  gcc
 *
 *         Author:  Idriss Daoudi
 *   Organization:  Argonne National Laboratory
 *
 * =====================================================================================
 */

int get_cpus (struct device** devices, hwloc_topology_t topology, hwloc_obj_t object, int index)
{
    char type[STR_SIZE];
    unsigned long long size = 0;
    
    int topology_depth = hwloc_topology_get_depth(topology);
    
    for (int i = 0; i < topology_depth; i++)
    {
        devices[index] = malloc(sizeof(struct device));

        int nb = hwloc_get_nbobjs_by_depth(topology, i);
        object = hwloc_get_obj_by_depth(topology, i, nb-1);
        hwloc_obj_type_snprintf(type, sizeof(type), object, 0);
        const char* model = hwloc_obj_get_info_by_name(object, "CPUModel");
        const char* backend = hwloc_obj_get_info_by_name(object, "Backend");
        
        if (object->name == NULL)
        {
            strcpy(devices[index]->name, "None");
        }
        else
        {
            strcpy(devices[index]->name, object->name);
        }
        strcpy(devices[index]->type, type);
        if (model == NULL)
        {
            strcpy(devices[index]->model, "None");
        }
        else
        {
            strcpy(devices[index]->model, model);
        }
        if (backend == NULL)
        {
            strcpy(devices[index]->backend, "None");
        }
        else
        {
            strcpy(devices[index]->backend, backend);
        }
        if (hwloc_obj_type_is_cache(object->type))
        {
            size = ((double)object->attr->cache.size / 1024);
        }
        else{
            size = 0;
        }
        devices[index]->size = size;
        devices[index]->amount = nb;
        devices[index]->id = 0;
        
        index++;
    }
    return index;
}
