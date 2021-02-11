{
  nrmSupport ? false
, pkgs ? (import <hnrm/default.nix> { })
, drv ?
  (import <hnrm/shell.nix> {
    inherit pkgs;
    experiment = true;
    analysis = false;
    jupyter = false;
  })
}:
let xpctl = import ./xpctl.nix;
in drv.overrideAttrs (o: {
  buildInputs =
    o.buildInputs
    ++ [ (pkgs.amg.override { nrmSupport = nrmSupport; }) ]
    ++ xpctl pkgs;
})
