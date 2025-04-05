{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.programs.lazygit;
in
{
  options.programs.lazygit = {
    enable = lib.mkEnableOption "lazygit, a simple terminal UI for git commands";

    package = lib.mkPackageOption pkgs "lazygit" { };

    settings = lib.options.mkConfigOption {
      format = pkgs.formats.yaml { };
      description = ''
        Lazygit configuration.

        See https://github.com/jesseduffield/lazygit/blob/master/docs/Config.md for documentation.
      '';
    };
  };

  config = lib.mkIf cfg.enable {
    environment = {
      systemPackages = [ cfg.package ];
      etc = lib.mkIf (cfg.settings.raw != { }) {
        "xdg/lazygit/config.yml".source = cfg.settings.source;
        "xdg/lazygit/config2.yml".text = cfg.settings.source.text;
      };
    };
  };

  meta = {
    maintainers = with lib.maintainers; [ linsui ];
  };
}
