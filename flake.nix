{
  description = "simple python parallelism";

  nixConfig = {
    substituters = [
      "https://cache.nixos.org/?priority=1&want-mass-query=true"
      "https://attic.alicehuston.xyz/cache-nix-dot?priority=4&want-mass-query=true"
      "https://nix-community.cachix.org/?priority=10&want-mass-query=true"
    ];
    trusted-substituters = [
      "https://cache.nixos.org"
      "https://attic.alicehuston.xyz/cache-nix-dot"
      "https://nix-community.cachix.org"
    ];
    trusted-public-keys = [
      "cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY="
      "cache.alicehuston.xyz:SJAm8HJVTWUjwcTTLAoi/5E1gUOJ0GWum2suPPv7CUo=%"
      "cache-nix-dot:Od9KN34LXc6Lu7y1ozzV1kIXZa8coClozgth/SYE7dU="
      "nix-community.cachix.org-1:mB9FSh9qf2dCimDSUo8Zy7bkq5CX+/rkCWyvRCYg3Fs="
    ];
  };

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs = {
        flake-utils.follows = "flake-utils";
        nixpkgs.follows = "nixpkgs";
      };
    };
  };

  outputs =
    inputs@{
      self,
      nixpkgs,
      flake-utils,
      ...
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        lib = pkgs.lib;
        poetry2nix = inputs.poetry2nix.lib.mkPoetry2Nix { inherit pkgs; };

        p2nix_defaults = {
          projectDir = ./.;
          python = pkgs.python312;
          overrides = poetry2nix.overrides.withDefaults (
            _: prev: lib.genAttrs [ "ruff" ] (package: prev.${package}.override { preferWheel = true; })
          );
        };
      in
      {
        packages.default = poetry2nix.mkPoetryApplication p2nix_defaults;

        devShells.default =
          (
            poetry2nix.mkPoetryEnv p2nix_defaults
            // {
              editablePackageSources = {
                speedy_snake = ./speedy_snake.py;
              };
            }
          ).env.overrideAttrs
            (old: {
              buildInputs = with pkgs; [
                poetry
                just
                python312Packages.pudb
              ];
            });

        apps.default = {
          type = "app";
          program = "${self.packages.speedy_snake}/bin/validate_jeeves";
        };
      }
    )
    // {
      hydraJobs = import ./hydra/jobs.nix { inherit (self) inputs outputs; };
    };
}
