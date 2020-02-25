Expérimentations préliminaires hnrm/g5k
=======================================

2020-02-18

Installation
------------

(Re-)Prise en main de g5k
^^^^^^^^^^^^^^^^^^^^^^^^^

On a besoin de modifier des permissions bas-niveau (droits root) : on utilise
le mécanisme déploiement.
(cf. https://www.grid5000.fr/w/Getting_Started#Deploying_your_nodes_to_get_root_access_and_create_your_own_experimental_environment)

.. code:: bash

   # réservation
   lux.g5k $ oarsub -I -l nodes=1,walltime=3:00 -t deploy

   # déploiement d'une image minimale
   lux.g5k $ kadeploy3 -f ${OAR_NODE_FILE} -e debian10-x64-min -k


J'ajoute les paquets :command:`aptitude` et :command:`tmux` pour simplifier les
installations et éviter les désagréments d'une déconnexion.


.. note::
   À terme, il faudra créer une image dédiée pour les expériences : ça peut
   être une image NixOS (cf. travail d'Olivier Richard), ou à défaut une image
   Debian adaptée.
   Il se pose la question de la version du noyau Linux par exemple (v4.x sur
   les Debian stable vs. v5.x).


Installation de :command:`hnrm`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

install Nix
"""""""""""

- install :command:`curl`

- :code:`mkdir -m 0755 /nix`

.. warning::
   I had issues to install Nix as root, create a user and install sudo?

----

2020-02-19

Installation
------------

Les tests d'installation sont fait sur un vieux cluster pour ne pas pénaliser
les autres utilisateurs.

À terme, il faut penser faire les expériences sur différentes générations de
processeurs.

déploiement
  .. code:: bash
     lux.g5k $ oarsub -I -l nodes=1,walltime=3:00 -t deploy
     lux.g5k $ kadeploy3 -f ${OAR_NODE_FILE} -e debian10-x64-min -k
     lux.g5k $ ssh -l root $(cat ${OAR_NODE_FILE} | head -1)


On installe quelques paquets *utiles*.

.. code:: bash
   node.lux.g5k # apt install bash-completion tmux


On travaille dans une session :command:`tmux` pour éviter les problèmes de
connexion.

.. code:: bash
   node.lux.g5k # tmux -2u new -s nix-install


Pour circonvenir aux problèmes d'installation de :command:`nix`, on installe
:commande:`sudo` et on crée un utilisateur `exp-runner`.

.. code:: bash

   node.lux.g5k # apt install sudo
   node.lux.g5k # adduser --quiet --disabled-password --gecos exp-runner exp-runner
   node.lux.g5k # adduser exp-runner sudo
   node.lux.g5k # echo "%sudo   ALL=(ALL:ALL) NOPASSWD: ALL" > /etc/sudoers.d/nopasswd
   node.lux.g5k # chmod 0440 /etc/sudoers.d/nopasswd
   node.lux.g5k # visudo --check --quiet


On installe :command:`nix` à proprement parler.

.. code:: bash

   # apt install curl
   # su - exp-runner -c 'sh <(curl https://nixos.org/nix/install) --no-daemon'


Quelques autres dépendances

.. code:: bash

   node.lux.g5k # apt install git

Installation de hnrm

.. code:: bash

   # su - exp-runner
   $ git clone https://xgitlab.cels.anl.gov/argo/hnrm.git
   $ cd hnrm
   $ git submodule init
   $ git submodule update

----

2020-02-20

identification CPU
^^^^^^^^^^^^^^^^^^

Sur les architectures x86, on peut utiliser l'instruction `cpuid` pour
identifier clairement le processeur.
Elle était renseignée dans le document
`AP-485 Intel® Processor Identification and the CPUID Instruction
<https://www.intel.com/content/www/us/en/processors/processor-identification-cpuid-instruction-note.html>`__,
et se trouve maintenant dans la description des instructions Intel (volume 2A).
C'est le mécanisme utilisé pour renseigner :file:`/proc/cpuinfo`.
On peut utiliser le paquet :command:`cpuid` pour avoir plus d'informations.

.. todo:: Ajouter le dump du CPUID dans le workflow expérimental

----

2020-02-21

déploiement automatique
^^^^^^^^^^^^^^^^^^^^^^^

- déployer sur g5k (voir ci-dessus)
- copier :file:`install-run-g5k.sh` dans :file:`/opt`
- depuis le nœud en root, executer :file:`/opt/install-run-g5k.sh`
- créer un tunnel ssh :samp:`ssh {g5k_site_frontend} -N -L {local_port}:{g5k_node}:{jupyter_port}`
  (par exemple, `ssh lux.g5k -N -L 8888:petitprince-5:8888`)
  :see:`https://www.grid5000.fr/w/SSH#Forwarding_a_local_port`

.. todo::
   il faut diviser le script en 2 parties :
     - la partie install en tant que root à basculer sur kameleon pour
       constuire une image
     - le reste dans un script pour faire tourner les trucs (utiliser un
       tag/sha plutôt que le nom de la branche à terme)

.. todo::
   réflexion sur les capabilities de nrmd

----

2020-02-25

étude des capabilities nécessaire pour nrmd
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

cf. :manpage:`capabilities(7)`

.. warning::
   :command:`nrmd` est un script python : il faut donc travailler sur les
   capabilities de l'interpréteur, voire packager :command:`nrmd` comme un
   binaire (`freezing <https://docs.python-guide.org/shipping/freezing/>`__)

On trace avec :command:`capable` les vérifications faites (cf. :file:`nrmd.caps`).
C'est un outils développé par Brendan Gregg
(cf. http://www.brendangregg.com/blog/2016-10-01/linux-bcc-security-capabilities.html),
packagé par Debian dans `bpfcc-tools` (attention il faut aussi installer
:samp:`linux-headers-{kernel-version}-all`).

L'exécutable doit appartenir à `root:root`.

Particularité du fait qu'on travaille sur l'interpréteur Python, il faut
aussi permettre l'héritage des capabilities (`+i`) pour les transmettre aux
sous-processus.

L'unique capability identifié pour le moment est `CAP_DAC_OVERRIDE`, afin de
naviguer dans la hiérarchie :file:`/sys/devices/virtual/powercap/`
