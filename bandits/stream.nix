{

pkgs ? (import ../../hnrm/default.nix { }),

drv ? (import ../../hnrm/shell.nix {
  inherit pkgs;
  experiment = true;
}) }:
drv.overrideAttrs (o: {

  buildInputs = o.buildInputs
    ++ [ (pkgs.stream.override { iterationCount = "16000"; }) ];

})
