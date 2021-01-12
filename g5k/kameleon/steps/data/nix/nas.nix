{ hnrmHome, pkgs ? (import (hnrmHome + /default.nix) { }), drv ?
  (import (hnrmHome + /shell.nix) {
    inherit pkgs;
    experiment = true;
    analysis = false;
    jupyter = false;
  }) }:
let xpctl = import ./xpctl.nix;
in drv.overrideAttrs
(o: { buildInputs = o.buildInputs ++ [ pkgs.nas ] ++ xpctl pkgs; })
