{
  description = "iCal upcoming events parser";

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
        icalUpcoming = pkgs.writeScriptBin "ical-upcoming" ''
          #!${pythonEnv}/bin/python
          ${builtins.readFile ./ical_upcoming.py}
        '';
        
      in
      {
        # Default package
        packages.default = icalUpcoming;
        
        # Development shell
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pythonEnv
            pkgs.git
          ];
          
          shellHook = ''
            echo "iCal upcoming events parser development environment"
            echo "Available commands:"
            echo "  pytest                    - Run tests"
            echo "  pytest --cov=ical_upcoming - Run tests with coverage"
            echo "  python ical_upcoming.py   - Run script directly"
            echo ""
            echo "Usage examples:"
            echo "  cat calendar.ics | python ical_upcoming.py"
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
          ${pythonEnv}/bin/pytest tests/ -v --cov=ical_upcoming --cov-report=html --cov-report=term
        '';
        
        # Apps
        apps = {
          default = {
            type = "app";
            program = "${icalUpcoming}/bin/ical-upcoming";
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