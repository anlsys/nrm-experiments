Automatisation de la création de l'image g5k
============================================

2020-03-05

Prise en main de kameleon
-------------------------

On suit le tutoriel du wiki g5k
https://www.grid5000.fr/w/Environments_creation_using_Kameleon_and_Puppet

étapes suivies
  - deploiement de l'image debian10-x64-std
  - installation de kameleon https://github.com/grid5000/environments-recipes/blob/master/tools/setup_grid5000.sh
  - création de l'image

.. code-block:: console

   # kameleon template repo add grid5000 https://github.com/grid5000/environments-recipes.git
   # mkdir my_recipes
   # cd my_recipes/
   # kameleon new debian10-x64-nix grid5000/debian10-x64-min.yaml
   # mkdir -p steps/setup

   # # put nix_single-user.yaml under steps/setup/
   # # edit recipe as needed

   # # create a tmpfs for build (speed build time)
   # mkdir /mnt/kameleon-build
   # mount -t tmpfs -o size=20G kameleon-build /mnt/kameleon-build

   # kameleon build --build-path=/mnt/kameleon-build --enable-cache debian10-x64-nix.yaml
