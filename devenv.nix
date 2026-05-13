{ pkgs, ... }:
let
  shell =
    { pkgs, ... }:
    {
      packages = [
        pkgs.gnumake
        pkgs.maven
        pkgs.google-java-format
        pkgs.nixfmt
        pkgs.prettier
        pkgs.treefmt
        pkgs.xmlformat
        pkgs.black
        pkgs.nodejs
      ];

      enterTest = ''
        mvn test
      '';
    };
in
{
  languages.java.enable = true;
  languages.java.jdk.package = pkgs.jdk21;

  languages.python.enable = true;
  languages.python.venv.enable = true;
  languages.python.venv.requirements = ''
    robotframework-robocop
    -e ./python
  '';

  profiles.shell.module = {
    imports = [ shell ];
  };
}
