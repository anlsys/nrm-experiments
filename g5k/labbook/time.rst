GNU `time` measures
===================

We use GNU `time` to measure some global characteristics of the benchmark run.
The output of time relates to the whole execution.

The output is in the CSV format, and obtained as follow:

.. code:: console

   $ echo 'cmd,retcode,elapsed.time,system.time,user.time,cpu.share,avg.mem,avg.rss,max.rss,avg.data,avg.text,avg.stack,page.size,major.page.faults,minor.page.faults,swaps,fs.inputs,fs.outputs,sock.rcvd,sock.sent,signals,time.ctx.switch,io.ctx.switch' > time.csv
   $ command time --output=time.csv --append --format='"%C",%x,%e,%S,%U,%P,%K,%t,%M,%D,%X,%p,%Z,%F,%R,%W,%I,%O,%r,%s,%k,%c,%w' -- <benchmark>


We do not use the `%E` specifier, as it is redundant with `%e`.

.. warning::
   Be careful not not use the :command:`bash` builtin.
   This is avoided in th example thanks to the :command:`command` builtin.


Command-related
---------------

+-----------+---------+------+-------------------------------------------------------------+
| specifier | column  | unit | details                                                     |
+===========+=========+======+=============================================================+
| %C        | cmd     |      | Name and command line arguments of the command being timed. |
+-----------+---------+------+-------------------------------------------------------------+
| %x        | retcode |      | Exit status of the command.                                 |
+-----------+---------+------+-------------------------------------------------------------+


Time-related
------------

+-----------+--------------+--------+-------------------------------------------------------------------------------------------------------+
| specifier | column       | unit   | details                                                                                               |
+===========+==============+========+=======================================================================================================+
| %e        | elapsed.time | second | Elapsed real (wall clock) time used by the process, in seconds.                                       |
+-----------+--------------+--------+-------------------------------------------------------------------------------------------------------+
| %S        | system.time  | second | Total number of CPU-seconds used by the system on behalf of the process (in kernel mode), in seconds. |
+-----------+--------------+--------+-------------------------------------------------------------------------------------------------------+
| %U        | user.time    | second | Total number of CPU-seconds that the process used directly (in user mode), in seconds.                |
+-----------+--------------+--------+-------------------------------------------------------------------------------------------------------+
| %P        | cpu.share    |        | Percentage of the CPU that this job got.                                                              |
|           |              |        | This is just user + system times divided by the total running time.                                   |
|           |              |        | It also prints a percentage sign.                                                                     |
+-----------+--------------+--------+-------------------------------------------------------------------------------------------------------+


Memory-related
--------------

+-----------+-------------------+----------+----------------------------------------------------------------------------------------------------------------+
| specifier | column            | unit     | details                                                                                                        |
+===========+===================+==========+================================================================================================================+
| %K        | avg.mem           | kilobyte | Average total (data+stack+text) memory use of the process, in Kilobytes.                                       |
+-----------+-------------------+----------+----------------------------------------------------------------------------------------------------------------+
| %t        | avg.rss           | kilobyte | Average resident set size of the process, in Kilobytes.                                                        |
+-----------+-------------------+----------+----------------------------------------------------------------------------------------------------------------+
| %M        | max.rss           | kilobyte | Maximum resident set size of the process during its lifetime, in Kilobytes.                                    |
+-----------+-------------------+----------+----------------------------------------------------------------------------------------------------------------+
| %D        | avg.data          | kilobyte | Average size of the process's unshared data area, in Kilobytes.                                                |
+-----------+-------------------+----------+----------------------------------------------------------------------------------------------------------------+
| %X        | avg.text          | kilobyte | Average amount of shared text in the process, in Kilobytes.                                                    |
+-----------+-------------------+----------+----------------------------------------------------------------------------------------------------------------+
| %p        | avg.stack         | kilobyte | Average unshared stack size of the process, in Kilobytes.                                                      |
+-----------+-------------------+----------+----------------------------------------------------------------------------------------------------------------+
| %Z        | page.size         | byte     | System's page size, in bytes.                                                                                  |
|           |                   |          | This is a per-system constant, but varies between systems.                                                     |
+-----------+-------------------+----------+----------------------------------------------------------------------------------------------------------------+
| %F        | major.page.faults |          | Number of major, or I/O-requiring, page faults that occurred while the process was running.                    |
|           |                   |          | These are faults where the page has actually migrated out of primary memory.                                   |
+-----------+-------------------+----------+----------------------------------------------------------------------------------------------------------------+
| %R        | minor.page.faults |          | Number of minor, or recoverable, page faults.                                                                  |
|           |                   |          | These are pages that are not valid (so they fault) but which have not yet been claimed by other virtual pages. |
|           |                   |          | Thus the data in the page is still valid but the system tables must be updated.                                |
+-----------+-------------------+----------+----------------------------------------------------------------------------------------------------------------+
| %W        | swaps             |          | Number of times the process was swapped out of main memory.                                                    |
+-----------+-------------------+----------+----------------------------------------------------------------------------------------------------------------+


I/O-related
-----------

+-----------+------------+------+----------------------------------------------------+
| specifier | column     | unit | details                                            |
+===========+============+======+====================================================+
| %I        | fs.inputs  |      | Number of file system inputs by the process.       |
+-----------+------------+------+----------------------------------------------------+
| %O        | fs.outputs |      | Number of file system outputs by the process.      |
+-----------+------------+------+----------------------------------------------------+
| %r        | sock.rcvd  |      | Number of socket messages received by the process. |
+-----------+------------+------+----------------------------------------------------+
| %s        | sock.sent  |      | Number of socket messages sent by the process.     |
+-----------+------------+------+----------------------------------------------------+


OS-related
----------

+-----------+-----------------+------+---------------------------------------------------------------------------------------------------------------------------------+
| specifier | column          | unit | details                                                                                                                         |
+===========+=================+======+=================================================================================================================================+
| %k        | signals         |      | Number of signals delivered to the process.                                                                                     |
+-----------+-----------------+------+---------------------------------------------------------------------------------------------------------------------------------+
| %c        | time.ctx.switch |      | Number of times the process was context-switched involuntarily (because the time slice expired).                                |
+-----------+-----------------+------+---------------------------------------------------------------------------------------------------------------------------------+
| %w        | io.ctx.switch   |      | Number of times that the program was context-switched voluntarily, for instance while waiting for an I/O operation to complete. |
+-----------+-----------------+------+---------------------------------------------------------------------------------------------------------------------------------+
