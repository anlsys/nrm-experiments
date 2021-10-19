# development shell, includes aml dependencies and dev-related helpers
{ pkgs ? import ./. { } }:
with pkgs;
mkShell {
  nativeBuildInputs = [ ];
  buildInputs = [
    nrm-core
    nrm-python
    libnrm
    nrm-extra
    hwloc
    linuxPackages.perf
  ];
}
