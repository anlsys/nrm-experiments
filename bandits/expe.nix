{

pkgs ? (import ../../hnrm.git/default.nix { }),

drv ? (import ../../hnrm.git/shell.nix {
  inherit pkgs;
  experiment = true;
  analysis = false;
  jupyter = false;
}) }:
drv.overrideAttrs (o: {

  buildInputs = o.buildInputs ++ [
    (pkgs.stream.override { iterationCount = "16000"; problemSize="80000000"; })
    # pkgs.amg
    pkgs.nas
  ];

})
