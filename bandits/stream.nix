let pkgs = (import ../../../dev/default.nix { });
in pkgs.hack.overrideAttrs (o: {

  buildInputs = o.buildInputs
    ++ [ (pkgs.stream.override { iterationCount = "40"; })];

})
