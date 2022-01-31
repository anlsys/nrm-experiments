{ stdenv, autoreconfHook, pkgconfig, zeromq, gfortran }:
stdenv.mkDerivation {
  src = fetchGit {
    url = "https://github.com/anlsys/libnrm.git";
    ref = "refs/tags/v0.7.0";
  };
  name = "libnrm";
  nativeBuildInputs = [ autoreconfHook pkgconfig ];
  buildInputs = [ zeromq gfortran ];
}
