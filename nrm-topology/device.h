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
    char type[STR_SIZE];
    char name[STR_SIZE];
    char model[STR_SIZE];
    char backend[STR_SIZE];
    double size; // In kB
    int amount; // For CPUs
    int id;     // For GPUs
};

