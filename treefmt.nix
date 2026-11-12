# treefmt-nix module, see https://github.com/numtide/treefmt-nix
{ ... }:
{
  projectRootFile = "flake.nix";
  programs.nixfmt.enable = true;
  programs.black.enable = true;
  programs.mdformat.enable = true;
}
