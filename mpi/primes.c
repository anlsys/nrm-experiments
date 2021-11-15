/*
 * =====================================================================================
 *
 *       Filename:  main.c
 *
 *    Description:  
 *
 *        Version:  1.0
 *        Created:  28/10/2021 16:13:43
 *       Revision:  none
 *       Compiler:  gcc
 *
 *         Author:  YOUR NAME (), 
 *   Organization:  
 *
 * =====================================================================================
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <inttypes.h>
#include <time.h>
#include <sched.h>
#include "mpi.h"

#define LIMIT     36
#define FIRST     0

void time_stamp(int rank, int n)
{
	long ms; // Milliseconds
	time_t s;  // Seconds
	struct timespec spec;

	clock_gettime(CLOCK_REALTIME, &spec);

	s  = spec.tv_sec;
	ms = round(spec.tv_nsec / 1.0e6); // Convert nanoseconds to milliseconds
	if (ms > 999) {
		s++;
		ms = 0;
	}
	char name[128];
	int size, cpu;

	cpu = sched_getcpu();
	printf("************************\n");
	printf("Time: %"PRIdMAX".%03ld\n", (intmax_t)s, ms);
	printf("Rank: %d\n", rank);
	printf("Checked: %d\n", n);
	printf("Scope: %d\n", cpu);
	
	//fprintf(file, "Time: %"PRIdMAX".%03ld\n", (intmax_t)s, ms);
	//fprintf(file, "Rank: %d\n", rank);
	//fprintf(file, "Checked: %d\n", n);
	//fprintf(file, "Scope: %d\n", cpu);
	//fprintf(file, "\n");

}

int isprime(int n) {
	int i = 0;
	int racine = 0;
	if (n > 10) 
	{
		racine = (int) sqrt(n);
		for (i = 3; i <= racine; i = i+2)
		{
			if ((n%i) == 0)
			{
				return 0;
			}
		}
		return 1;
	}
	else
		return 0;
}

int main ()
{
	int   nranks,
	      rank,
	      n,
	      prime_counter,
	      pcsum,
	      found,
	      maxprime,
	      mystart,
	      jump;

	double start_time, end_time;

	MPI_Init(NULL, NULL);
	MPI_Comm_rank(MPI_COMM_WORLD, &rank);
	MPI_Comm_size(MPI_COMM_WORLD, &nranks);

	if (((nranks % 2) != 0) || ((LIMIT % nranks) != 0)) 
	{
		printf("Number of ranks must be even and must divide the LIMIT!\n");
		MPI_Finalize();
		exit(0);
	}

	start_time = MPI_Wtime();
	mystart = (rank*2)+1;
	jump = nranks*2;
	prime_counter=0;
	found = 0;

	//FILE *file;
	//file = fopen("./log.rec", "w+");

	if (rank == FIRST)
	{
		// Jump the first 4 primes (<10)
		prime_counter = 4;
		for (n = mystart; n <= LIMIT; n = n+jump)
		{
			if (isprime(n)) 
			{
				prime_counter++;
				found = n;
				//printf("%d\n",found);
			}
			time_stamp(rank, n);
		}
		MPI_Reduce(&prime_counter, &pcsum, 1, MPI_INT, MPI_SUM, FIRST, MPI_COMM_WORLD);
		MPI_Reduce(&found, &maxprime, 1, MPI_INT, MPI_MAX, FIRST, MPI_COMM_WORLD);
		end_time = MPI_Wtime();
		printf("Found %d primes in %.6lfs\n", pcsum, end_time-start_time);
	}

	if (rank > FIRST) 
	{
		for (n = mystart; n <= LIMIT; n = n+jump) 
		{
			if (isprime(n)) 
			{
				prime_counter++;
				found = n;
				//printf("%d\n",found);
			}
			time_stamp(rank, n);
		}
		MPI_Reduce(&prime_counter, &pcsum, 1, MPI_INT, MPI_SUM, FIRST, MPI_COMM_WORLD);
		MPI_Reduce(&found, &maxprime, 1, MPI_INT, MPI_MAX, FIRST, MPI_COMM_WORLD);
	}

	//fclose(file);
	MPI_Finalize();
}
