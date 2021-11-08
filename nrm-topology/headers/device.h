/*
 * =====================================================================================
 *
 *       Filename:  device.h
 *
 *    Description:  Device structure definition
 *
 *        Version:  1.0
 *        Created:  21/10/2021 18:58:51
 *       Revision:  none
 *       Compiler:  gcc
 *
 *         Author:  Idriss Daoudi
 *   Organization:  Argonne National Laboratory
 *
 * =====================================================================================
 */

#define STR_SIZE 1024

struct device
{
	int resource_id; // Unique resource scope ID
	char name[STR_SIZE];
	char type[STR_SIZE];
    char backend[STR_SIZE];
	char memory[MAX][STR_SIZE];
	char compute[MAX][STR_SIZE];
	char logical_index[MAX][STR_SIZE];
};

