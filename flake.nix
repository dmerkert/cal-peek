{
  description = "cal-peek: Calendar event viewer";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        python = pkgs.python311;
        
        pythonPackages = python.pkgs;
        
        # Python dependencies
        dependencies = with pythonPackages; [
          icalendar
          python-dateutil
          pytz
        ];
        
        # Test dependencies
        testDependencies = with pythonPackages; [
          pytest
          pytest-cov
        ];
        
        # Create Python environment
        pythonEnv = python.withPackages (ps: dependencies ++ testDependencies);
        
        # Main script
        calPeek = pkgs.writeScriptBin "cal-peek" ''
          #!${pythonEnv}/bin/python
          ${builtins.readFile ./cal_peek.py}
        '';
        
      in
      {
        # Default package
        packages.default = calPeek;
        
        # Development shell
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pythonEnv
            pkgs.git
          ];
          
          shellHook = ''
            echo "cal-peek: Calendar event viewer development environment"
            echo "Available commands:"
            echo "  pytest                    - Run tests"
            echo "  pytest --cov=cal_peek    - Run tests with coverage"
            echo "  python cal_peek.py        - Run script directly"
            echo ""
            echo "Usage examples:"
            echo "  cat calendar.ics | python cal_peek.py"
            echo "  cat calendar.ics | nix run ."
            echo ""
          '';
        };
        
        # Test runner
        packages.test = pkgs.writeScriptBin "run-tests" ''
          #!${pkgs.bash}/bin/bash
          cd ${./.}
          ${pythonEnv}/bin/pytest tests/ -v
        '';
        
        # Test with coverage
        packages.test-cov = pkgs.writeScriptBin "run-tests-coverage" ''
          #!${pkgs.bash}/bin/bash
          cd ${./.}
          ${pythonEnv}/bin/pytest tests/ -v --cov=cal_peek --cov-report=html --cov-report=term
        '';
        
        # Apps
        apps = {
          default = {
            type = "app";
            program = "${calPeek}/bin/cal-peek";
          };
          
          test = {
            type = "app";
            program = "${self.packages.${system}.test}/bin/run-tests";
          };
          
          test-cov = {
            type = "app";
            program = "${self.packages.${system}.test-cov}/bin/run-tests-coverage";
          };
        };
        
        # Formatter
        formatter = pkgs.nixpkgs-fmt;
      });
}