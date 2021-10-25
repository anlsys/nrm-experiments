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
	int counter = 0;

	while ((object = hwloc_get_next_osdev(topology, object)) != NULL)
	{
		devices[index] = malloc(sizeof(struct device));
		int i = 0;
		int id = 0;
		const char* size = NULL;
		const char* compute_units = NULL;

		hwloc_obj_type_snprintf(type, sizeof(type), object, 0);
		if ((strcmp(type, "DMA") == 0) || (strcmp(type, "Block") == 0) || (strcmp(type, "Net") == 0))
		{
			continue;
		}

		const char* model = hwloc_obj_get_info_by_name(object, "GPUModel");
		const char* backend = hwloc_obj_get_info_by_name(object,"Backend");
		
		strcpy(devices[index]->type, type);
		model != 0 ? strcpy(devices[index]->name, model) : strcpy(devices[index]->name, "None");
		backend != 0 ? strcpy(devices[index]->backend, backend) : strcpy(devices[index]->backend, "None");
		devices[index]->resource_id = object->gp_index;		

		if ((sscanf(object->name, "cuda%d", &id) == 1)
				|| (sscanf(object->name, "rsmi%d", &id) == 1)
				|| (sscanf(object->name, "nvml%d", &id) == 1)
				|| (sscanf(object->name, "ve%d", &id) == 1)
				|| (sscanf(object->name, "ze%d", &id) == 1)
				|| (sscanf(object->name, "card%d", &id) == 1)
				|| (sscanf(object->name, "renderD%d", &id) == 1))
		{
			size = hwloc_obj_get_info_by_name(object,"CUDAGlobalMemorySize");
			compute_units = hwloc_obj_get_info_by_name(object,"CUDAMultiProcessors");
		}
		else if (sscanf(object->name, "opencl%dd%d", &i, &id) == 2)
		{
			size = hwloc_obj_get_info_by_name(object,"OpenCLGlobalMemorySize");
			compute_units = hwloc_obj_get_info_by_name(object,"OpenCLComputeUnits");
		}
		size != NULL ? strcpy(devices[index]->memory[counter], size) : strcpy(devices[index]->memory[counter], "0");
		compute_units != NULL ? strcpy(devices[index]->compute[counter], compute_units) : strcpy(devices[index]->compute[counter], "0");
		
		counter++;
		index++;
	}
	return index;
}
