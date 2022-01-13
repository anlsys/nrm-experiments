{ stdenv, autoreconfHook, pkgconfig, libnrm, openmp }:
stdenv.mkDerivation {
  src = ~/Argonne/nrm-benchmarks;
  name = "nrm-benchmarks";
  nativeBuildInputs = [ autoreconfHook pkgconfig openmp ];
  buildInputs = [ libnrm ];
  CFLAGS = "-ggdb -O0";
  dontStrip = true;
}
