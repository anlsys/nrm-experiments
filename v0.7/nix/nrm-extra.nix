{ stdenv, autoreconfHook, pkgconfig, gfortran, libnrm, openmp, mpich2, zeromq }:
stdenv.mkDerivation {
  src = fetchGit {
    url = "https://github.com/anlsys/nrm-extra.git";
    ref = "refs/tags/v0.7.0";
  };
  name = "nrm-extra";
  nativeBuildInputs = [ autoreconfHook pkgconfig libnrm mpich2 openmp ];
  buildInputs = [ gfortran ] ++ libnrm.buildInputs;
}
