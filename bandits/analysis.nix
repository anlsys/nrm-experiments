{

pkgs ? (import ../../hnrm/default.nix { }),

drv ? (import ../../hnrm/shell.nix {
  inherit pkgs;
  experiment = false;
  analysis = true;
  jupyter = false;
}) }:
drv.overrideAttrs (o: {

  buildInputs = o.buildInputs ++ [

    (pkgs.stream.override { iterationCount = "16000"; })

    pkgs.amg

  ];

})
