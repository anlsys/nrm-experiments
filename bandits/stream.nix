let pkgs = (import ../../../dev/default.nix { });
in pkgs.hack.overrideAttrs (o: {

  buildInputs = o.buildInputs
    ++ [ (pkgs.expe.override { iterationCount = "16000"; })];
    #++ [ (pkgs.stream.override { iterationCount = "1000"; })];

})
