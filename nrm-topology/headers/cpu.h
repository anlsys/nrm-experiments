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
	char type_current_object[STR_SIZE];
	unsigned long long size = 0;

	int topology_depth = hwloc_topology_get_depth(topology);

	for (int i = 0; i < topology_depth; i++)
	{
		int nb = hwloc_get_nbobjs_by_depth(topology, i);
		for (int j = 0; j < nb; j++)
		{
			object = hwloc_get_obj_by_depth(topology, i, j);
			hwloc_obj_type_snprintf(type, sizeof(type), object, 0);
			if (strcmp(type, "Package") == 0)
			{
				devices[index] = malloc(sizeof(struct device));

				int nb_of_packages = hwloc_get_nbobjs_by_type(topology, object->type);
				const char* model = hwloc_obj_get_info_by_name(object, "CPUModel");
				const char* backend = hwloc_obj_get_info_by_name(object, "Backend");

				strcpy(devices[index]->type, type);
				model != NULL ? strcpy(devices[index]->name, model) : strcpy(devices[index]->name, "");
				backend != NULL ? strcpy(devices[index]->backend, backend) : strcpy(devices[index]->backend, "");
				devices[index]->resource_id = object->gp_index;

				int memory_counter = 0;
				int compute_counter = 0;
				int core_arity = 0;
				char compute_units_to_string[STR_SIZE], size_to_string[STR_SIZE], logical_index_to_string[STR_SIZE];

				int arity = object->arity;
				for (int k = 0; k < arity; k++)
				{
					if (object->type == HWLOC_OBJ_PU)
					{
						break;
					}
					hwloc_obj_t current_object = object->children[k];
					hwloc_obj_type_snprintf(type_current_object, sizeof(type_current_object), current_object, 0);

					hwloc_obj_t core_object = current_object;
					while (core_object->type == HWLOC_OBJ_CORE)
					{
						core_arity += core_object->arity;
						if (core_object->next_cousin == NULL)
						{
							break;
						}
						else
						{
							core_object = core_object->next_cousin;
						}
					}

					if (hwloc_obj_type_is_cache(current_object->type))
					{
						strcpy(devices[index]->memory[memory_counter], type_current_object);
						int compute_units = hwloc_get_nbobjs_by_type(topology, current_object->type);
						sprintf(compute_units_to_string, "%d", compute_units/nb_of_packages);
						strcpy(devices[index]->memory[memory_counter + 1], compute_units_to_string);
						size = ((double)current_object->attr->cache.size / 1024);
						sprintf(size_to_string, "%llu", size);
						strcpy(devices[index]->memory[memory_counter + 2], size_to_string);

						memory_counter += 3;	
					}
					else
					{
						strcpy(devices[index]->compute[compute_counter], type_current_object);
						int compute_units = hwloc_get_nbobjs_by_type(topology, current_object->type);
						sprintf(compute_units_to_string, "%d", compute_units/nb_of_packages);
						strcpy(devices[index]->compute[compute_counter + 1], compute_units_to_string);
						int li_counter = 0;
						while (current_object->type == HWLOC_OBJ_PU)
						{
							sprintf(logical_index_to_string, "%d", current_object->logical_index);
							strcpy(devices[index]->logical_index[li_counter], logical_index_to_string);
							if (current_object->next_cousin != NULL && li_counter < core_arity)
							{
								current_object = current_object->next_cousin;
								li_counter++;
							}
							else
							{
								break;
							}
						}
						compute_counter += 2;	
					}
					object = object->children[k];
					k = -1;
				}
				index++;		
			}
		}
	}
	return index;
}
