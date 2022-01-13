{ stdenv, autoreconfHook, pkgconfig, zeromq, gfortran }:
stdenv.mkDerivation {
  src = fetchGit {
    url = "https://github.com/anlsys/libnrm.git";
  };
  name = "libnrm";
  dontStrip = true;
  nativeBuildInputs = [ autoreconfHook pkgconfig gfortran ];
  propagatedBuildInputs = [ zeromq ];
  CFLAGS = "-ggdb -O0";
}
