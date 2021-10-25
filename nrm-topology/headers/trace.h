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
	file = fopen("./test.rec", "w+"); // GNU Recutils format
	for (int i = 0; i < index; i++)
	{
		fprintf(file, "ID: %d\n", devices[i]->resource_id);
		fprintf(file, "Type: %s\n", devices[i]->type);
		fprintf(file, "Name: %s\n", devices[i]->name);
		fprintf(file, "Backend: %s\n", devices[i]->backend);
		fprintf(file, "Memory: ");
		for (int j = 0; j < MAX; j++)
		{
			if (strlen(devices[i]->memory[j]) != 0)
			{
				if (j != 0)
				{
					fprintf(file, ", ");
				}
				fprintf(file, "%s", devices[i]->memory[j]);
			}
			else
			{
				break;
			}
		}
		fprintf(file, "\n");
		fprintf(file, "Compute: ");
		for (int j = 0; j < MAX; j++)
		{
			if (strlen(devices[i]->compute[j]) != 0)
			{
				if (j != 0)
				{
					fprintf(file, ", ");
				}
				fprintf(file, "%s", devices[i]->compute[j]);
			}
			else
			{
				break;
			}
		}
		fprintf(file, "\n");
	}
	fclose(file);
}
