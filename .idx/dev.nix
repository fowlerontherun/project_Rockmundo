{ pkgs, ... }: {
  channel = "stable-24.05";
  packages = [
    pkgs.python311
    pkgs.python311Packages.pip
  ];
  env = {};
  idx = {
    extensions = [];
    previews = {
      enable = true;
      previews = {};
    };
    workspace = {
      onCreate = {};
      onStart = {};
    };
  };
}
