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


Base image deployment
---------------------

From the shell of the chosen site frontend (here Luxembourg):

.. code-block:: console

   $ cluster=petitprince
   $ oarsub -I -l nodes=1,walltime=3:00 -p "cluster='${cluster}'" -t deploy
   [ADMISSION RULE] Modify resource description with type constraints
   [ADMISSION_RULE] Resources properties : \{'resources' => [{'resource' => 'host','value' => '1'}],'property' => 'type = \'default\''}
   [ADMISSION RULE] Job properties : ((cluster='petitprince') AND deploy = 'YES') AND maintenance = 'NO'
   Generate a job key...
   OAR_JOB_ID=198385
   Interactive mode: waiting...
   Starting...
   Connect to OAR job 198385 via the node frontend
   $ kadeploy3 -f ${OAR_NODE_FILE} -e debian10-x64-min -k
   Deployment #D-e2f6675e-327e-49dd-9eb2-3527edda9de3 started
   Grab the key file /home/rbleuse/.ssh/authorized_keys
   Launching a deployment on petitprince-14.luxembourg.grid5000.fr
   Performing a Deploy[SetDeploymentEnvUntrusted] step
     switch_pxe
     reboot
      * Performing a soft reboot on petitprince-14.luxembourg.grid5000.fr
     wait_reboot
     send_key_in_deploy_env
     create_partition_table
     format_deploy_part
     mount_deploy_part
     format_swap_part
   End of step Deploy[SetDeploymentEnvUntrusted] after 202s
   Performing a Deploy[BroadcastEnvKascade] step
     send_environment
      * Broadcast time: 10s
     manage_admin_post_install
     manage_user_post_install
     check_kernel_files
     send_key
     install_bootloader
     sync
   End of step Deploy[BroadcastEnvKascade] after 37s
   Performing a Deploy[BootNewEnvKexec] step
     switch_pxe
     umount_deploy_part
     mount_deploy_part
     kexec
     wait_reboot
   End of step Deploy[BootNewEnvKexec] after 29s
   End of deployment for petitprince-14.luxembourg.grid5000.fr after 268s
   End of deployment on cluster petitprince after 269s
   Deployment #D-e2f6675e-327e-49dd-9eb2-3527edda9de3 done
   
   The deployment is successful on nodes
   petitprince-14.luxembourg.grid5000.fr


It takes about 5—10 minutes to deploy the image on the node.


Installation & Start of Jupyter notebook
----------------------------------------

Copy the script :file:`install-run-g5k.sh` to :file:`/opt` on the deployed node
(on the example run above, it is `petitprince-14.luxembourg.grid5000.fr`).

Execute as root the script, it takes about 10—30 minutes to install.

.. code-block:: console

   # /opt/install-run-g5k.sh
   …
   [I 11:03:51.641 NotebookApp] Writing notebook server cookie secret to /home/exp-runner/.local/share/jupyter/runtime/notebook_cookie_secret
   [I 11:03:53.463 NotebookApp] Serving notebooks from local directory: /opt/hnrm
   [I 11:03:53.463 NotebookApp] The Jupyter Notebook is running at:
   [I 11:03:53.463 NotebookApp] http://(petitprince-14.luxembourg.grid5000.fr or 127.0.0.1):8888/?token=6bfa61e58c1c1347bdba53c063eece33d625e36d4d3bc3ad
   [I 11:03:53.463 NotebookApp] Use Control-C to stop this server and shut down all kernels (twice to skip confirmation).
   [C 11:03:53.469 NotebookApp] 
       
       To access the notebook, open this file in a browser:
           file:///home/exp-runner/.local/share/jupyter/runtime/nbserver-19745-open.html
       Or copy and paste one of these URLs:
           http://(petitprince-14.luxembourg.grid5000.fr or 127.0.0.1):8888/?token=6bfa61e58c1c1347bdba53c063eece33d625e36d4d3bc3ad


Once started, the Jupyter notebook displays the URL to use to access it (along
with a token).

Connection to the Jupyter notebook
----------------------------------

The Grid'5000 internal network is isolated from the rest of the Internet.
To access the notebook, we rely on the ability of :command:`ssh` to forward
traffic (see https://www.grid5000.fr/w/SSH#Forwarding_a_local_port).

We suppose the :command:`ssh` configuration works.

From the local machine (replace elements between brackets as needed), the
command looks like :samp:`ssh {g5k_site_frontend} -N -L {local_port}:{g5k_node}:{jupyter_port}`).

With the example above:

.. code-block:: console

   $ ssh lux.g5k -N -L 8888:petitprince-14:8888


Modify the URL given by Jupyter by replacing the domain/port with localhost and
the chosen local port.
Access this modified URL from the local web browser.


.. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. .. ..

.. |g5k| replace:: `Grid'5000`_
.. _Grid'5000: https://www.grid5000.fr/
