
{ pkgs ? import <nixpkgs> {} }:

let
  my-dev-env = import ./.idx/dev.nix;
in
pkgs.mkShell {
  buildInputs = (my-dev-env { pkgs = pkgs; }).packages;
}
