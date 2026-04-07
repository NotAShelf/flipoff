{
  description = "Flipoff - Hand gesture detection app packaged with uv2nix";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs?ref=nixos-unstable";

    # uv2nix and its dependencies. The unfortunate (and frankly frustrating) reality
    # is that uv2nix cannot work without pyproject-nix and pyproject-build-systems.
    # I have many people to blame, but I choose to blame Python tooling for not more
    # easily managable.
    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
    };

    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
    };
  };

  outputs = {
    self,
    nixpkgs,
    uv2nix,
    pyproject-nix,
    pyproject-build-systems,
  }: let
    inherit (nixpkgs) lib;
    forAllSystems = lib.genAttrs ["x86_64-linux" "aarch64-linux"];

    # Per-system configuration generator
    mkSystemConfig = system: let
      pkgs = nixpkgs.legacyPackages.${system};
      python = pkgs.python311;

      # Load the uv workspace
      workspace = uv2nix.lib.workspace.loadWorkspace {
        workspaceRoot = ./.;
      };

      # Base Python package set
      pythonBase = pkgs.callPackage pyproject-nix.build.packages {
        inherit python;
      };

      # Create overlays from uv.lock
      overlay = workspace.mkPyprojectOverlay {
        sourcePreference = "wheel";
      };

      editableOverlay = workspace.mkEditablePyprojectOverlay {
        root = "$REPO_ROOT";
      };

      # Compose Python set with build systems
      pythonSet = pythonBase.overrideScope (
        lib.composeManyExtensions [
          pyproject-build-systems.overlays.wheel
          overlay
        ]
      );

      editablePythonSet = pythonSet.overrideScope editableOverlay;

      # Virtual environments
      virtualenv = pythonSet.mkVirtualEnv "flipoff-env" workspace.deps.default;
      devVirtualenv = editablePythonSet.mkVirtualEnv "flipoff-dev-env" workspace.deps.all;

      # It's better to fetch the mediapipe models with Nix so that we can avoid
      # doing this in the runtime. Will be passed to the Python program via the
      # FLIPOFF_MODEL_PATH variable.
      mediapipe-model = pkgs.fetchurl {
        url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task";
        sha256 = "1qfd0wvcz2yg5hrfxk2420sfncl1d4sc7psx7c4mgif3h00a7hpv";
      };

      # Runtime dependencies with specific outputs
      runtimeDeps = with pkgs; [
        systemdLibs.out
        libglvnd.dev
        libxcb.out
        libxkbcommon.out
        libx11.out
        libxcursor.out
        libxext.out
        libxi.out
        libxrandr.out
        libxrender.out
        libice.out
        libsm.out
        glib.dev
      ];

      # Dev shell dependencies (includes runtime + extra dev tools)
      devDeps =
        runtimeDeps
        ++ (with pkgs; [
          glib.bin
        ]);

      # Common library path for LD_LIBRARY_PATH
      libPath = lib.makeLibraryPath (with pkgs; [
        systemdLibs
        libglvnd
        libxcb
        libxkbcommon
        libx11
        libxcursor
        libxext
        libxi
        libxrandr
        libxrender
        libice
        libsm
        glib
      ]);

      # Common environment variables
      commonEnv = {
        FLIPOFF_MODEL_PATH = "${mediapipe-model}";
        QT_QPA_PLATFORM = "xcb";
      };
    in {
      inherit pkgs python virtualenv devVirtualenv pythonSet editablePythonSet workspace runtimeDeps devDeps libPath commonEnv mediapipe-model;
    };
  in {
    packages = forAllSystems (
      system: let
        cfg = mkSystemConfig system;
        inherit (cfg) pkgs virtualenv runtimeDeps libPath mediapipe-model;
      in {
        flipoff = pkgs.stdenv.mkDerivation {
          name = "flipoff";
          version = "1.0.0";
          src = lib.fileset.toSource {
            root = ./.;
            fileset = lib.fileset.unions [
              ./src
              ./pyproject.toml
              ./uv.lock
            ];
          };

          buildInputs = [virtualenv] ++ runtimeDeps;
          nativeBuildInputs = [pkgs.makeWrapper];

          buildCommand = ''
            mkdir -p $out/bin $out/lib

            # Copy source files
            cp -rv $src $out/lib/

            # Create the wrapper script
            makeWrapper ${virtualenv}/bin/python $out/bin/flipoff \
              --add-flags "-m flipoff" \
              --prefix LD_LIBRARY_PATH : "${libPath}" \
              --set FLIPOFF_MODEL_PATH "${mediapipe-model}" \
              --set QT_QPA_PLATFORM "xcb"
          '';
        };

        default = self.packages.${system}.flipoff;
      }
    );

    devShells = forAllSystems (
      system: let
        cfg = mkSystemConfig system;
        inherit (cfg) pkgs devVirtualenv editablePythonSet devDeps libPath commonEnv;
      in {
        default = pkgs.mkShell {
          packages = [devVirtualenv pkgs.uv] ++ devDeps;

          env = {
            inherit (commonEnv) FLIPOFF_MODEL_PATH QT_QPA_PLATFORM;
            UV_NO_SYNC = "1";
            UV_PYTHON = editablePythonSet.python.interpreter;
            UV_PYTHON_DOWNLOADS = "never";
          };

          # This tomfoolery is "recommended" by uv2nix to allow using the virtualenv
          # from inside the Nix dev shell. Frankly, this sucks.
          shellHook = ''
            unset PYTHONPATH
            export REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
            export LD_LIBRARY_PATH="${libPath}"
          '';
        };
      }
    );
  };
}
