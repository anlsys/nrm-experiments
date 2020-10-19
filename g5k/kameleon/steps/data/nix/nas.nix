{ hnrmHome, pkgs ? (import (hnrmHome + /default.nix) { }), drv ?
  (import (hnrmHome + /shell.nix) {
    inherit pkgs;
    experiment = true;
    analysis = false;
    jupyter = false;
  }) }:
drv.overrideAttrs (o: { buildInputs = o.buildInputs ++ [ pkgs.nas ]; })
