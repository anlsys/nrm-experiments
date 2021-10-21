/*
 * =====================================================================================
 *
 *       Filename:  trace.h
 *
 *    Description:  Print trace to file
 *
 *        Version:  1.0
 *        Created:  21/10/2021 23:53:53
 *       Revision:  none
 *       Compiler:  gcc
 *
 *         Author:  Idriss Daoudi
 *   Organization:  
 *
 * =====================================================================================
 */

void print_to_file(struct device** devices, int index)
{
	FILE *file;
	file = fopen("./test.log", "w+");
	for (int i = 0; i < index; i++)
	{
		fprintf(file, "Type: %s\n", devices[i]->type);
		fprintf(file, "Name: %s\n", devices[i]->name);
		fprintf(file, "Model: %s\n", devices[i]->model);
		fprintf(file, "Backend: %s\n", devices[i]->backend);
		fprintf(file, "MemorySize: %f\n", devices[i]->size);
		fprintf(file, "Amount: %d\n", devices[i]->amount);
		fprintf(file, "ID: %d\n", devices[i]->id);
		fprintf(file, "\n");
	}
	fclose(file);
}
