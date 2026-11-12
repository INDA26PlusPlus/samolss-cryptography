# Heavily inspired by:
# https://github.com/DeterminateSystems/zero-to-nix/blob/main/nix/templates/pkg/rust/flake.nix
# and
# https://github.com/numtide/treefmt-nix
{

  description = "Simple flake";

  inputs = {
    nixpkgs.url = "github:Nixos/nixpkgs/nixpkgs-unstable";
    treefmt-nix = {
      url = "github:numtide/treefmt-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    rust-overlay = {
      url = "github:oxalica/rust-overlay";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    inputs@{
      self,
      nixpkgs,
      rust-overlay,
      treefmt-nix,
    }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];

      forAllSystems =
        f:
        nixpkgs.lib.genAttrs systems (
          system:
          f {
            pkgs = import nixpkgs {
              inherit system;
            };
          }
        );

      treefmtEval = forAllSystems (
        { pkgs }:
        treefmt-nix.lib.evalModule pkgs ./treefmt.nix
      );
    in
    {
      formatter = forAllSystems (
        { pkgs }:
        treefmtEval.${pkgs.system}.config.build.wrapper
      );

      checks = forAllSystems (
        { pkgs }: {
          formatter = treefmtEval.${pkgs.system}.config.build.check self;
        }
      );

      devShells = forAllSystems (
        { pkgs }: {
          default = pkgs.mkShell {
            buildInputs = with pkgs; [
              python314
              python314Packages.cryptography
              python314Packages.requests
              python314Packages.flask
            ];
          };
        }
      );

    };
}
