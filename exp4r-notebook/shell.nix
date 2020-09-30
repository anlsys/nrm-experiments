{ nixpkgs ? (builtins.fetchTarball
  "https://github.com/NixOS/nixpkgs/archive/20.03.tar.gz") }:
let

  pkgs = import nixpkgs {

    config = {
      ihaskell = {
        packages = ps:
          with ps; [
            ihaskell-charts
            ihaskell-widgets
            ad
            Chart
            Chart-diagrams
            lens
            protolude
            generic-lens
            generic-data
            refined
            command-qq
            hbandit
            probability
            random-fu
            HaTeX
            ihaskell-hatex
            statistics
            xls
            datasets
            intervals
            neat-interpolation
            pretty-simple
          ];
      };
    };

    overlays = [
      (_: pkgs: {
        haskellPackages = pkgs.haskell.packages.ghc865.override {
          overrides = self: super:
            with pkgs.haskell.lib; rec {
              hbandit = self.callCabal2nix "hbandit" ../../hbandit { };
              refined = unmarkBroken super.refined;
              ihaskell = unmarkBroken super.ihaskell;
              datasets = unmarkBroken super.datasets;
              streaming-cassava = doJailbreak( unmarkBroken super.streaming-cassava);
              panpipe = (unmarkBroken (doJailbreak super.panpipe));
              panhandle = (unmarkBroken
                (doJailbreak (dontCheck super.panhandle))).overrideAttrs (_: {
                  inherit (pkgs.nix-update-source.fetch ./panhandle.json) src;
                });
              vinyl = doJailbreak (unmarkBroken super.vinyl);
              ihaskell-blaze = unmarkBroken super.ihaskell-blaze;
              ihaskell-charts = unmarkBroken super.ihaskell-charts;
              ihaskell-widgets = unmarkBroken super.ihaskell-widgets;
              ihaskell-inline-r = unmarkBroken super.ihaskell-inline-r;
              ihaskell-diagrams = unmarkBroken super.ihaskell-diagrams;
              ihaskell-display = unmarkBroken super.ihaskell-display;
              ihaskell-hatex = unmarkBroken super.ihaskell-hatex;
            };
        };
      })

    ];

  };
in pkgs.haskellPackages.shellFor {
  packages = p: [
    (pkgs.haskellPackages.callCabal2nix "deps" ./.{ })
  ];
  buildInputs = [
    pkgs.haskellPackages.ghcid
    pkgs.texlive.combined.scheme-full
    pkgs.rubber
    pkgs.xfig
    pkgs.fig2dev
    pkgs.pdf2svg
    pkgs.ihaskell
    pkgs.pythonPackages.nbconvert
    pkgs.pythonPackages.sympy
    pkgs.ormolu
  ];
}

