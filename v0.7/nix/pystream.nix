{ stdenv, python3Packages, nrm-python }:
python3Packages.buildPythonPackage {
  src = ../../pySTREAM;
  name = "pystream";
  buildInputs = [];
  propagatedBuildInputs = [
    nrm-python
    python3Packages.cython
  ];
}
