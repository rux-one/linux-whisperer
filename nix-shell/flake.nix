{
  description = "Pytorch with cuda";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  };
  outputs = { self, nixpkgs }:
  
  let 
   pkgs = import nixpkgs { system = "x86_64-linux"; config.allowUnfree = true; };
  in
  { 
    devShells."x86_64-linux".default = pkgs.mkShell {
      LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
        pkgs.stdenv.cc.cc
        "/run/opengl-driver"
      ];
        
      venvDir = ".venv";
      packages = with pkgs; [
        python312    
        python312Packages.venvShellHook
        python312Packages.pip
        python312Packages.numpy
        python312Packages.pyaudio
        python312Packages.pyqt6
        python312Packages.pynput
        virtualenv
        uv

        qt6.qtbase
        qt6.full
        qt6.qtwayland
        python312
        python312Packages.pyqt6
        xorg.libxcb
        xorg.libXinerama
        xorg.xcbutil
        xorg.xcbutilimage
        xorg.xcbutilkeysyms
        xorg.xcbutilrenderutil
        xorg.xcbutilwm
        xcb-util-cursor
        xorg.xcursorgen
        libxkbcommon
        xcbutilxrm
        mesa
        qt6.qtwayland

        ffmpeg
        pkg-config
        glibc
      ];

      shellHook = ''                                                                                                  
          export QT_QPA_PLATFORM=wayland
          export QT_PLUGIN_PATH=$(nix eval --raw nixpkgs#qt6.qtbase)/lib/qt-6/plugins

          cd ~/code/linux-whisperer
          . venv/bin/activate
      '';
    };

  };
}
