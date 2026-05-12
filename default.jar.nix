{
  buildMavenRepositoryFromLockFile,
  jdk_headless,
  maven,
  stdenv,
}:
let
  mavenRepository = buildMavenRepositoryFromLockFile { file = ./mvn2nix.lock; };

  # Exclude directories not needed for the Maven build.
  filteredSrc = builtins.filterSource (
    path: _type:
    let
      base = baseNameOf path;

      # Excluded by basename anywhere in the tree (safe: these names never
      # appear as meaningful subdirectory names inside src/main/resources).
      excludedAnywhere = [
        ".devenv"
        ".git"
        ".idea"
        "__pycache__"
        "node_modules"
        "target"
        "tmp"
      ];

      # Excluded only when they appear directly under the repo root.
      root = builtins.toString ./.;
      excludedAtRoot = [
        "dependency-reduced-pom.xml"
        "default.jar.nix"
        "default.nix"
        "devenv.local.nix"
        "devenv.local.yaml"
        "devenv.nix"
        "devenv.yaml"
        "docs"
        "flake.lock"
        "flake.nix"
        "log.html"
        "mvn2nix.lock"
        "output.xml"
        "report.html"
      ];
    in
    !(builtins.elem base excludedAnywhere)
    && !(builtins.elem path (map (name: "${root}/${name}") excludedAtRoot))
  ) ./.;
in
stdenv.mkDerivation rec {
  pname = "operaton-bpm-extension-robot";
  version = "1.0-SNAPSHOT";

  # The Maven shade plugin (profile: shade) produces this exact filename.
  name = "${pname}-${version}-fat.jar";

  src = filteredSrc;

  buildInputs = [
    jdk_headless
    maven
  ];

  # The graalpy-maven-plugin downloads robotframework and
  # robotframework-pythonlibcore from PyPI at build time into the GraalPy
  # VFS venv.  Disable the Nix sandbox so that network access is available
  # during the build phase.
  __noChroot = true;

  buildPhase = ''
    find . -print0 | xargs -0 touch
    echo "mvn -Pshade package -DskipTests --offline -Dmaven.repo.local=${mavenRepository}"
    mvn -Pshade package -DskipTests --offline \
      -Dmaven.repo.local=${mavenRepository}
  '';

  installPhase = ''
    mv target/${name} $out
    jar i $out
  '';
}
