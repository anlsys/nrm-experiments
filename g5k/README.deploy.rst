==================
Deploying on |g5k|
==================

Experimenting with :command:`hnrm` requires to access and tune parameters of
the OS.
We rely on the *deploy* job type of Grid'5000 to control the software
environment.

The procedure documented here is tailored for the deployment of hnrm notebooks,
please consider the Wiki of Grid'5000 as the Truth
(https://www.grid5000.fr/w/Getting_Started#Deploying_your_nodes_to_get_root_access_and_create_your_own_experimental_environment).

As :command:`hnrm` relies on RAPL, care needs to be taken when choosing the
Grid'5000 cluster.


Image deployment
----------------

From the shell of the chosen site fronted (here Grenoble):

.. code-block:: console

   $ cluster=dahu
   $ walltime=1:00
   $
   $ oarsub -I -l "nodes=1,walltime=${walltime}" -p "cluster='${cluster}'" -t deploy
   [ADMISSION RULE] Modify resource description with type constraints
   [ADMISSION_RULE] Resources properties : \{'property' => 'type = \'default\'','resources' => [{'resource' => 'host','value' => '1'}]}
   [ADMISSION RULE] Job properties : ((cluster='dahu') AND deploy = 'YES') AND maintenance = 'NO'
   Generate a job key...
   OAR_JOB_ID=1923747
   Interactive mode: waiting...
   Starting...
   Connect to OAR job 1923747 via the node frontend
   $
   $ kadeploy3 -f ${OAR_NODE_FILE} -u rbleuse -e debian10-x64-hnrm -k
   Deployment #D-081b9bd2-9b1f-4c53-a355-fdeb7c2b1fde started
   Grab the key file /home/rbleuse/.ssh/authorized_keys
   Launching a deployment on dahu-32.grenoble.grid5000.fr
   Performing a Deploy[SetDeploymentEnvUntrusted] step
     switch_pxe
     reboot
      * Performing a soft reboot on dahu-32.grenoble.grid5000.fr
     wait_reboot
     send_key_in_deploy_env
     create_partition_table
     format_deploy_part
     mount_deploy_part
     format_swap_part
   End of step Deploy[SetDeploymentEnvUntrusted] after 205s
   Performing a Deploy[BroadcastEnvKascade] step
     send_environment
      * Broadcast time: 78s
     manage_admin_post_install
     manage_user_post_install
     check_kernel_files
     send_key
     install_bootloader
     sync
   End of step Deploy[BroadcastEnvKascade] after 97s
   Performing a Deploy[BootNewEnvKexec] step
     switch_pxe
     umount_deploy_part
     mount_deploy_part
     kexec
     wait_reboot
   End of step Deploy[BootNewEnvKexec] after 30s
   End of deployment for dahu-32.grenoble.grid5000.fr after 332s
   End of deployment on cluster dahu after 333s
   Deployment #D-081b9bd2-9b1f-4c53-a355-fdeb7c2b1fde done
   
   The deployment is successful on nodes
   dahu-32.grenoble.grid5000.fr

It takes about 5—10 minutes to deploy the image on the node.


Jupyter notebook
----------------

Launching Jupyter notebook
^^^^^^^^^^^^^^^^^^^^^^^^^^

All required software is installed on the deployed image.
From the frontend, the notebook can be launched with the following command:

.. note::
   The image was in this example deployed on `dahu-32`, adapt the command as
   required.

.. code-block:: console

   $ ssh root@dahu-32 /opt/xplaunch jupyter
   …
   Sourcing python-catch-conflicts-hook.sh
   Sourcing python-remove-bin-bytecode-hook.sh
   Sourcing setuptools-build-hook
   Using setuptoolsBuildPhase
   Sourcing pip-install-hook
   Using pipInstallPhase
   Sourcing python-imports-check-hook.sh
   Using pythonImportsCheckPhase
   Sourcing setuptools-check-hook
   Using setuptoolsCheckPhase
   /nix/store/vilh5ays3ymz3xkwk0fri2a70lha7pfc-stdenv-linux/setup: line 795: /run/user/0/env-vars: Permission denied
   [I 16:35:02.687 NotebookApp] Serving notebooks from local directory: /opt/hnrm-expe-0.3
   [I 16:35:02.687 NotebookApp] The Jupyter Notebook is running at:
   [I 16:35:02.687 NotebookApp] http://dahu-32.grenoble.grid5000.fr:8888/?token=9c1d649ddfcb2857a9c26e5b96e90315e11cb7ee42dab5cd
   [I 16:35:02.687 NotebookApp]  or http://127.0.0.1:8888/?token=9c1d649ddfcb2857a9c26e5b96e90315e11cb7ee42dab5cd
   [I 16:35:02.687 NotebookApp] Use Control-C to stop this server and shut down all kernels (twice to skip confirmation).
   [C 16:35:02.690 NotebookApp]
       
       To access the notebook, open this file in a browser:
           file:///home/xprunner/.local/share/jupyter/runtime/nbserver-2658-open.html
       Or copy and paste one of these URLs:
           http://dahu-32.grenoble.grid5000.fr:8888/?token=9c1d649ddfcb2857a9c26e5b96e90315e11cb7ee42dab5cd
        or http://127.0.0.1:8888/?token=9c1d649ddfcb2857a9c26e5b96e90315e11cb7ee42dab5cd


Once started, the Jupyter notebook displays the URL to use to access it (along
with a token).
This token changes on each run.


Connecting to the Jupyter notebook
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The Grid'5000 internal network is isolated from the rest of the Internet.
To access the notebook, we rely on the ability of :command:`ssh` to forward
traffic (see https://www.grid5000.fr/w/SSH#Forwarding_a_local_port).

We suppose the :command:`ssh` configuration works.

From the local machine (replace elements between brackets as needed), the
command looks like :samp:`ssh {g5k_site_frontend} -N -L {local_port}:{g5k_node}:{jupyter_port}`.

With the example above:

.. code-block:: console

   $ ssh gre.g5k -N -L 8888:dahu-32:8888


By default, Jupyter uses the `8888` port.
Copy the URL with the localhost IP (i.e., http://127.0.0.1:8888/?token=9c1d649ddfcb2857a9c26e5b96e90315e11cb7ee42dab5cd), and access it from the local web browser.


Static gain experiment
----------------------

Supported benchmarks
  - Algebraic multigrid benchmark (AMG): `amg`
  - NAS Parallel Benchmarks, EP: `ep.A.x`, `ep.B.x`, `ep.C.x`, `ep.D.x`, `ep.E.x`
  - STREAM benchmark: `stream_c`


Wrapped command
^^^^^^^^^^^^^^^

The general form of the command is :samp:`/opt/xplaunch static-gain --powercap={pcap} -- {cmd}`

.. code-block:: console

   $ ssh root@dahu-32 /opt/xplaunch static-gain --powercap=150 -- stream_c -n 10_000 -s 33_554_432


Manual launch
^^^^^^^^^^^^^

If required, the commands may be manually launched.

The commands may be launched in their own nix environment, without nrm.
If this is the case (e.g., to test the compilation result) a single nix shell is required.

If the command is to be launched with nrm, then two nix shells are required: a
shell for the daemon, and a shell for the client.

The shell is started with the following command:

.. code:: console

   nix-shell \
        --pure \
        --arg hnrmHome <path/to/nrm> \
        --argstr iterationCount 10000 \
        --argstr problemSize 33554432 \
        <path/to/nix-shell/definition>


If the benchmark requires libnrm instrumentation, the support is activated in
the nix-shell with `--arg nrmSupport true`.


The daemon is launched with:

.. code:: console

   nrmd -i -y <<< '{"raplCfg":{"raplActions":[{"microwatts":100000000}]},"verbose":"Info"}'


The application is launched with:

.. code:: console

   nrm run -i -y <<< '{"app":{"instrumentation":{"ratelimit":{"hertz":1000000}}}}' stream_c


.. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. ..

.. |g5k| replace:: `Grid'5000`_
.. _Grid'5000: https://www.grid5000.fr/
