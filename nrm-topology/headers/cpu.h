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

	// For each depth
	for (int i = 0; i < topology_depth; i++)
	{
		int nb = hwloc_get_nbobjs_by_depth(topology, i);
		// For each objects with depth i
		for (int j = 0; j < nb; j++)
		{
			object = hwloc_get_obj_by_depth(topology, i, j);
			hwloc_obj_type_snprintf(type, sizeof(type), object, 0);
			if (strcmp(type, "Package") == 0)
			{
				devices[index] = malloc(sizeof(struct device));
				
				const char* model = hwloc_obj_get_info_by_name(object, "CPUModel");
				const char* backend = hwloc_obj_get_info_by_name(object, "Backend");

				strcpy(devices[index]->type, type);
				strlen(model) > 0 ? strcpy(devices[index]->name, model) : strcpy(devices[index]->name, "None");
				backend != NULL ? strcpy(devices[index]->backend, backend) : strcpy(devices[index]->backend, "None");

				int memory_counter = 0;
				int compute_counter = 0;
				// Arity == children
				int arity = object->arity;
				int previous_arity = 0;
				char sarity[STR_SIZE], ssize[STR_SIZE];
				// For each child
				for (int k = 0; k < arity; k++)
				{
					if (object->type == HWLOC_OBJ_PU)
					{
						break;
					}
					hwloc_obj_t current_object = object->children[k];
					hwloc_obj_type_snprintf(type_current_object, sizeof(type_current_object), current_object, 0);
					printf("Type: %s\n", type_current_object);
				
					int my_arity = current_object->arity; //j'ai combien d'enfants
					if (hwloc_obj_type_is_cache(object->children[k]->type))
					{
						printf("is a cache\n");

						strcpy(devices[index]->memory[memory_counter + k], type_current_object);
						int cousins = hwloc_get_nbobjs_by_type(topology, object->children[k]->type);
						sprintf(sarity, "%d", cousins);
						printf("with arity: %d\n", cousins);
						strcpy(devices[index]->memory[memory_counter + 1 + k], sarity);
						size = ((double)current_object->attr->cache.size / 1024);
						printf("with size: %llu\n", size);
						sprintf(ssize, "%llu", size);
						strcpy(devices[index]->memory[memory_counter + 2 + k], ssize);
					}
					else
					{
						strcpy(devices[index]->compute[compute_counter + k], type_current_object);
						int cousins = hwloc_get_nbobjs_by_type(topology, object->children[k]->type);
						sprintf(sarity, "%d", cousins);
						strcpy(devices[index]->compute[compute_counter + 1 + k], sarity);
					}

					memory_counter += 3;	
					compute_counter += 2;	
					object = object->children[k];
					k = -1;
				}

				//if (object->name == NULL)
				//{
				//	strcpy(devices[index]->name, "None");
				//}
				//else
				//{
				//	strcpy(devices[index]->name, object->name);
				//}
				//strcpy(devices[index]->type, type);
				//if (model == NULL)
				//{
				//	strcpy(devices[index]->model, "None");
				//}
				//else
				//{
				//	strcpy(devices[index]->model, model);
				//}
				//if (backend == NULL)
				//{
				//	strcpy(devices[index]->backend, "None");
				//}
				//else
				//{
				//	strcpy(devices[index]->backend, backend);
				//}
				//if (hwloc_obj_type_is_cache(object->type))
				//{
				//	size = ((double)object->attr->cache.size / 1024);
				//}
				//else{
				//	size = 0;
				//}
				//devices[index]->size = size;
				//devices[index]->amount = nb;
				//devices[index]->id = 0;

				index++;		

			}
		}
	}
	return index;
}
