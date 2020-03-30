let pkgs = (import ../../../dev/default.nix { });
in pkgs.hack.overrideAttrs (o: {

  buildInputs = o.buildInputs
    ++ [ (pkgs.stream.override { iterationCount = "500"; })];
    #++ [ (pkgs.stream.override { iterationCount = "1000"; })];

})
