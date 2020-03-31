====================================
Building the experiments environment
====================================

The experiments are run with a custom image deployed on Grid'5000.
The image is built with :command:`kameleon`, as documented on the Wiki
(https://www.grid5000.f/w/Environments_creation_using_Kameleon_and_Puppet)


Building the image
------------------

The image is built on Grid'5000, as a normal user with an interactive
submission (:command:`oarsub -I`).
Some packages might be missing, one may install them with :command:`sudo-g5k`.

The steps to build the image are located under `kameleon`.

.. code-block:: console

   kameleon
   ├── debian10-x64-hnrm.yaml
   └── steps
       └── setup
           ├── hnrm.yaml
           └── nix_single-user.yaml
