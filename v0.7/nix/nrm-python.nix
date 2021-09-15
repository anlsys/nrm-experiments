{ stdenv, python3Packages, hwloc, linuxPackages, nrm-core }:
python3Packages.buildPythonPackage {
  src = fetchGit {
    url = "https://github.com/anlsys/nrm-python.git";
    rev = "a9f13f8577512a70bcea7f67a2c6c7d36573d32f";
  };
  name = "nrm-python";
  buildInputs = [ nrm-core ];
  propagatedBuildInputs = [
    nrm-core
    linuxPackages.perf
    python3Packages.tornado
    python3Packages.pyzmq
    python3Packages.pyyaml
    python3Packages.jsonschema
    python3Packages.msgpack
    python3Packages.warlock
  ];
  preBuild = ''
    substituteInPlace bin/nrmd \
      --replace "os.environ[\"NRMSO\"]" \"${nrm-core}/bin/nrm.so\"
    substituteInPlace nrm/tooling.py \
      --replace "os.environ[\"PYNRMSO\"]" \"${nrm-core}/bin/pynrm.so\"
  '';
}
