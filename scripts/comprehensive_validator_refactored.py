#!/usr/bin/env python3
"""
Comprehensive Project Validator (Refactored)
============================================

Refactored validation script using modular validators for better maintainability.
"""

import sys
from pathlib import Path
from typing import Dict, Any

# Add the validators directory to the path
sys.path.insert(0, str(Path(__file__).parent / "validators"))

from validators import (
    StructureValidator,
    FileValidator, 
    IntegrationValidator,
    ConfigValidator,
    TestValidator,
    SecurityValidator,
    PerformanceValidator
)


class ComprehensiveValidator:
    """Main comprehensive validator that orchestrates all validation modules."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = project_root
        self.validators = {
            'structure': StructureValidator(project_root),
            'files': FileValidator(project_root),
            'integration': IntegrationValidator(project_root),
            'config': ConfigValidator(project_root),
            'tests': TestValidator(project_root),
            'security': SecurityValidator(project_root),
            'performance': PerformanceValidator(project_root)
        }
        self.results = {
            "timestamp": None,
            "project_root": str(Path(project_root).resolve()),
            "validator_version": "2.1.0",
            "validation_modules": {},
            "summary": {
                "total_checks": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0,
                "critical_errors": 0,
                "recommendations": []
            }
        }
    
    def validate_all(self) -> Dict[str, Any]:
        """Run comprehensive validation suite using all modules."""
        print("🔍 Starting comprehensive project validation (Refactored)...")
        print("=" * 80)
        
        # Run all validators
        for name, validator in self.validators.items():
            print(f"\n📋 Running {name.title()} Validation...")
            print("-" * 40)
            
            if name == 'structure':
                validator.validate_project_structure()
                validator.validate_essential_files()
            elif name == 'files':
                validator.validate_runner_scripts()
                validator.validate_python_files()
                validator.validate_imports()
            elif name == 'integration':
                validator.validate_backend_integration()
                validator.validate_frontend_integration()
                validator.validate_api_consistency()
            elif name == 'config':
                validator.validate_configuration_completeness()
                validator.validate_environment_setup()
                validator.validate_dependency_management()
            elif name == 'tests':
                validator.validate_test_coverage()
                validator.validate_test_configuration()
                validator.validate_documentation_completeness()
                validator.validate_api_documentation()
            elif name == 'security':
                validator.validate_security_measures()
                validator.validate_docker_setup()
                validator.validate_production_readiness()
            elif name == 'performance':
                validator.validate_performance_configurations()
            
            # Collect results from this validator
            validator_results = validator.get_results()
            self.results["validation_modules"][name] = validator_results
            
            # Aggregate summary
            self._aggregate_results(validator_results)
        
        # Calculate final summary
        self._calculate_final_summary()
        
        # Display results
        self._display_results()
        
        return self.results
    
    def _aggregate_results(self, validator_results: Dict[str, Any]):
        """Aggregate results from a validator into the main results."""
        if "summary" in validator_results:
            summary = validator_results["summary"]
            self.results["summary"]["total_checks"] += summary.get("total_checks", 0)
            self.results["summary"]["passed"] += summary.get("passed", 0)
            self.results["summary"]["failed"] += summary.get("failed", 0)
            self.results["summary"]["warnings"] += summary.get("warnings", 0)
            self.results["summary"]["critical_errors"] += summary.get("critical_errors", 0)
            
            if "recommendations" in summary:
                self.results["summary"]["recommendations"].extend(summary["recommendations"])
    
    def _calculate_final_summary(self):
        """Calculate final summary statistics."""
        total = self.results["summary"]["total_checks"]
        passed = self.results["summary"]["passed"]
        failed = self.results["summary"]["failed"]
        warnings = self.results["summary"]["warnings"]
        critical = self.results["summary"]["critical_errors"]
        
        if total > 0:
            success_rate = (passed / total) * 100
            self.results["summary"]["success_rate"] = round(success_rate, 2)
        else:
            self.results["summary"]["success_rate"] = 0
        
        # Determine overall status
        if critical > 0:
            self.results["summary"]["overall_status"] = "CRITICAL"
        elif failed > 0:
            self.results["summary"]["overall_status"] = "FAILED"
        elif warnings > 0:
            self.results["summary"]["overall_status"] = "WARNING"
        else:
            self.results["summary"]["overall_status"] = "PASSED"
    
    def _display_results(self):
        """Display validation results in a formatted way."""
        print("\n" + "=" * 80)
        print("📊 VALIDATION SUMMARY")
        print("=" * 80)
        
        summary = self.results["summary"]
        
        print(f"Overall Status: {summary['overall_status']}")
        print(f"Success Rate: {summary['success_rate']}%")
        print(f"Total Checks: {summary['total_checks']}")
        print(f"✅ Passed: {summary['passed']}")
        print(f"❌ Failed: {summary['failed']}")
        print(f"⚠️  Warnings: {summary['warnings']}")
        print(f"🚨 Critical: {summary['critical_errors']}")
        
        if summary["recommendations"]:
            print(f"\n💡 Recommendations ({len(summary['recommendations'])}):")
            for i, rec in enumerate(summary["recommendations"][:5], 1):  # Show first 5
                print(f"  {i}. {rec}")
            if len(summary["recommendations"]) > 5:
                print(f"  ... and {len(summary['recommendations']) - 5} more")
        
        print("\n" + "=" * 80)
        
        # Show module breakdown
        print("📋 MODULE BREAKDOWN")
        print("-" * 40)
        for module_name, module_results in self.results["validation_modules"].items():
            if "summary" in module_results:
                module_summary = module_results["summary"]
                module_total = module_summary.get("total_checks", 0)
                module_passed = module_summary.get("passed", 0)
                module_failed = module_summary.get("failed", 0)
                module_warnings = module_summary.get("warnings", 0)
                
                if module_total > 0:
                    module_rate = (module_passed / module_total) * 100
                    print(f"{module_name.title():12} | {module_rate:5.1f}% | {module_passed:2d}P {module_failed:2d}F {module_warnings:2d}W")
                else:
                    print(f"{module_name.title():12} | No checks")
        
        print("=" * 80)
    
    def get_exit_code(self) -> int:
        """Get exit code based on validation results."""
        summary = self.results["summary"]
        
        if summary["critical_errors"] > 0:
            return 2  # Critical errors
        elif summary["failed"] > 0:
            return 1  # Failed checks
        else:
            return 0  # Success


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Comprehensive Project Validator")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--output", help="Output file for results (JSON)")
    parser.add_argument("--quiet", action="store_true", help="Quiet mode (minimal output)")
    
    args = parser.parse_args()
    
    validator = ComprehensiveValidator(args.project_root)
    results = validator.validate_all()
    
    if args.output:
        import json
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📄 Results saved to {args.output}")
    
    exit_code = validator.get_exit_code()
    if not args.quiet:
        print(f"\n🏁 Validation completed with exit code: {exit_code}")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

