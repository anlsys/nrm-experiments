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


Launching Jupyter notebook
--------------------------

All required software is installed on the deployed image.
From the frontend, the notebook can be launched with the following command:

.. note::
   The image was in this example deployed on `dahu-32`, adapt the command as
   required.

.. code-block:: console

   $ ssh root@dahu-32 -- runuser -u nix -- bash -l <<EOF
   > cd /opt/hnrm-master
   > nix-shell --run 'jupyter-notebook --no-browser --ip="0.0.0.0"'
   > EOF
   [I 10:36:36.778 NotebookApp] Serving notebooks from local directory: /opt/hnrm-master
   [I 10:36:36.778 NotebookApp] The Jupyter Notebook is running at:
   [I 10:36:36.778 NotebookApp] http://(dahu-32.grenoble.grid5000.fr or 127.0.0.1):8888/?token=47e1454cf0b3905d4870676209a008d9192235ff6fdb6a1a
   [I 10:36:36.778 NotebookApp] Use Control-C to stop this server and shut down all kernels (twice to skip confirmation).
   [C 10:36:36.780 NotebookApp]
   
       To access the notebook, open this file in a browser:
           file:///run/user/0/jupyter/nbserver-23248-open.html
       Or copy and paste one of these URLs:
           http://(dahu-32.grenoble.grid5000.fr or 127.0.0.1):8888/?token=47e1454cf0b3905d4870676209a008d9192235ff6fdb6a1a

Once started, the Jupyter notebook displays the URL to use to access it (along
with a token).


Connection to the Jupyter notebook
----------------------------------

The Grid'5000 internal network is isolated from the rest of the Internet.
To access the notebook, we rely on the ability of :command:`ssh` to forward
traffic (see https://www.grid5000.fr/w/SSH#Forwarding_a_local_port).

We suppose the :command:`ssh` configuration works.

From the local machine (replace elements between brackets as needed), the
command looks like :samp:`ssh {g5k_site_frontend} -N -L {local_port}:{g5k_node}:{jupyter_port}`.

With the example above:

.. code-block:: console

   $ ssh gre.g5k -N -L 8888:dahu-32:8888


Modify the URL given by Jupyter by replacing the domain/port with `localhost`
and the chosen local port.
Access this modified URL from the local web browser.


.. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. ..

.. |g5k| replace:: `Grid'5000`_
.. _Grid'5000: https://www.grid5000.fr/
