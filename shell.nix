{pkgs ? import <nixpkgs> {}}: let
  libsForPython = pkgs.lib.makeLibraryPath [
    pkgs.zlib
    pkgs.stdenv.cc.cc
    pkgs.openssl
    pkgs.bzip2
    pkgs.libxml2
    pkgs.xz
    pkgs.systemd
    pkgs.libxcb
    pkgs.glib
    pkgs.libxkbcommon
    pkgs.libx11
    pkgs.libxcursor
    pkgs.libxext
    pkgs.libxi
    pkgs.libxrandr
    pkgs.libxrender
    pkgs.libice
    pkgs.libsm
  ];

  # It's better to fetch the mediapipe models with Nix so that we can avoid
  # doing this in the runtime. Will be passed to the Python program via the
  # FLIPOFF_MODEL_PATH variable.
  mediapipe-model = pkgs.fetchurl {
    url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task";
    sha256 = "1qfd0wvcz2yg5hrfxk2420sfncl1d4sc7psx7c4mgif3h00a7hpv";
  };
in
  pkgs.mkShell {
    buildInputs = with pkgs; [
      python311
      uv
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
      glib.bin
    ];

    env = {
      LD_LIBRARY_PATH = "${libsForPython}:${pkgs.libglvnd}/lib";
      QT_QPA_PLATFORM = "xcb";
      UV_PYTHON_DOWNLOADS = "never";
      FLIPOFF_MODEL_PATH = "${mediapipe-model}";
    };
  }
