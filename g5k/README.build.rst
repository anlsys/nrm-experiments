====================================
Building the experiments environment
====================================

The experiments are run with a custom image deployed on Grid'5000.
The image is built with :command:`kameleon`, as documented on the Wiki
(https://www.grid5000.fr/w/Environments_creation_using_Kameleon_and_Puppet)


Building the image
==================

The image is built on Grid'5000, as a normal user with an interactive
submission (:command:`oarsub -I`).
Some packages might be missing, one may install them with :command:`sudo-g5k`.


:command:`kameleon` recipe
--------------------------

The steps to build the image are located under :file:`kameleon/`.

.. code-block:: console

   kameleon/
   ├── debian10-x64-hnrm.yaml
   └── steps
       └── setup
           ├── hnrm.yaml
           └── nix_multi-user.yaml


The recipe extends Grid'5000 ``min`` variant image.

As `command`:hnrm` is packaged with Nix, the :command:`kameleon` recipe starts
with a multi-user Nix installation (see :file:`steps/nix_multi-user.yaml`).

The installation of :command:`hnrm` retrieves the source, and triggers the
build to avoid rebuilding the whole stack on each deploy (see :file:`steps/hnrm.yaml`).
As :command:`hnrm` monitors and modifies low-level OS configuration, the Python
interpreter capabilities are updated accordingly.


preparing :file:`kameleon`
--------------------------

We suppose :command:`kameleon` is installed.

register Grid'5000 recipe repository
  .. code:: console

     $ kameleon repository add grid5000 https://gitlab.inria.fr/grid5000/environments-recipes.git
     Cloning into '/home/rbleuse/.kameleon.d/repos/grid5000'...
     remote: Enumerating objects: 44, done.
     remote: Counting objects: 100% (44/44), done.
     remote: Compressing objects: 100% (43/43), done.
     remote: Total 15305 (delta 15), reused 0 (delta 0), pack-reused 15261
     Receiving objects: 100% (15305/15305), 1.92 MiB | 8.89 MiB/s, done.
     Resolving deltas: 100% (9510/9510), done.

update Grid'5000 recipe repository
  .. code:: console

     $ kameleon repository update grid5000
     POST git-upload-pack (gzip 1172 to 657 bytes)
     remote: Enumerating objects: 39, done.
     remote: Counting objects: 100% (39/39), done.
     remote: Compressing objects: 100% (36/36), done.
     remote: Total 39 (delta 14), reused 5 (delta 2), pack-reused 0
     Unpacking objects: 100% (39/39), done.
     From https://gitlab.inria.fr/grid5000/environments-recipes
     …


building the image
------------------

.. code:: console

   $ # go to directory with kameleon recipe
   $ cd kameleon
   $ tree
   .
   ├── debian10-x64-hnrm.yaml
   └── steps
       └── setup
           ├── hnrm.yaml
           └── nix_multi-user.yaml

   2 directories, 3 files
   $ # retrieve steps from grid5000 recipe repository
   $ kameleon new debian10-x64-hnrm.yaml grid5000/from_grid5000_environment/base.yaml
         create  grid5000/from_grid5000_environment/base.yaml
         create  grid5000/steps/backend/qemu.yaml
         create  grid5000/steps/backend/VM.yaml
         create  grid5000/steps/aliases/defaults.yaml
         create  grid5000/steps/checkpoints/qemu.yaml
         create  grid5000/steps/bootstrap/prepare_ssh_to_out_context.yaml
         create  grid5000/steps/bootstrap/download_upstream_tarball.yaml
         create  grid5000/steps/bootstrap/create_appliance.yaml
         create  grid5000/steps/bootstrap/prepare_appliance.yaml
         create  grid5000/steps/bootstrap/start_qemu.yaml
         create  grid5000/steps/disable_checkpoint.yaml
         create  grid5000/steps/export/save_appliance_VM.yaml
         create  grid5000/steps/export/create_kadeploy_environment.yaml
         create  grid5000/steps/data/helpers/create_appliance.py
         create  grid5000/steps/data/qemu-sendkeys.rb
         create  grid5000/steps/data/helpers/export_appliance.py
         create  grid5000/steps/data/helpers/kaenv-customize.py
         create  grid5000/steps/env/bashrc
         create  grid5000/steps/env/functions.sh
       conflict  debian10-x64-hnrm.yaml
   Overwrite /home/rbleuse/kameleon/2020-07-03/debian10-x64-hnrm.yaml? (enter "h" for help) [Ynaqdhm] n
           skip  debian10-x64-hnrm.yaml
   $ # build the image
   $ kameleon build debian10-x64-hnrm.yaml
   Creating kameleon build directory : /home/rbleuse/kameleon/2020-07-03/build/debian10-x64-hnrm
   Starting build recipe 'debian10-x64-hnrm.yaml'
   Step 1 : bootstrap/_init_bootstrap/_init_0_create_appliance
   --> Running the step...
   Starting command: "bash"
   [local] The local_context has been initialized
   [local] virt-make-fs is /usr/bin/virt-make-fs
   Step 2 : bootstrap/_init_bootstrap/_init_1_create_appliance
   --> Running the step...
   [local] grub-mkstandalone is /usr/bin/grub-mkstandalone
   …
   Step 26 : setup/nix_multi-user/check_nix_install
   --> Running the step...
   …
   [in]  - system: `"x86_64-linux"`
   [in]  - host os: `Linux 4.19.0-9-amd64, Debian GNU/Linux, 10 (buster)`
   [in]  - multi-user?: `yes`
   [in]  - sandbox: `yes`
   [in]  - version: `nix-env (Nix) 2.3.6`
   [in]  - channels(root): `"nixpkgs-20.09pre233849.1d801806827"`
   [in]  - nixpkgs: `/nix/var/nix/profiles/per-user/root/channels/nixpkgs`
   [in]
   Step nix_multi-user took: 23 secs
   Step 27 : setup/hnrm/install_dependencies
   --> Running the step...
   …
   Step 29 : setup/hnrm/install_hnrm
   --> Running the step...
   …
   Step hnrm took: 1785 secs
   Step 30 : setup/_clean_setup/_clean_0_start_vm
   --> Running the step...
   …
   Step 33 : export/save_appliance_VM/save_appliance
   --> Running the step...
   [local] INFO: Creating /home/rbleuse/kameleon/2020-07-03/build/debian10-x64-hnrm/debian10-x64-hnrm.tar.gz
   …
   Step _clean_export took: 3 secs

   Successfully built 'debian10-x64-hnrm.yaml'
   Total duration : 2258 secs


Registering the image
=====================

Refer to the man pages of :command:`kaenv3`.

It is best to use the http://public.grenoble.grid5000.fr/ URL to locate the image file.
