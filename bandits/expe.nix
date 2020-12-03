{

pkgs ? (import ../../hnrm/default.nix { }),

drv ? (import ../../hnrm/shell.nix {
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
