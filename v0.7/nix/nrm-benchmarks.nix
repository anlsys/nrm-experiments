{ stdenv, autoreconfHook, pkgconfig, libnrm, zeromq, gfortran, openmp }:
stdenv.mkDerivation {
  src = ~/Argonne/nrm-benchmarks;
  name = "nrm-benchmarks";
  nativeBuildInputs = [ autoreconfHook pkgconfig libnrm openmp ];
  buildInputs = [ zeromq gfortran ] ++ libnrm.buildInputs;
}
