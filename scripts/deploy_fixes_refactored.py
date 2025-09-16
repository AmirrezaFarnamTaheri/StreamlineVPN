#!/usr/bin/env python3
"""
StreamlineVPN Deploy Fixes (Refactored)
=======================================

Refactored deployment script using modular components for better maintainability.
"""

import sys
import argparse
from pathlib import Path

# Add the deployment directory to the path
sys.path.insert(0, str(Path(__file__).parent / "deployment"))

from deployment import DeploymentManager, ContentGenerators, ValidationRunner


class StreamlineVPNDeployer:
    """Main deployment orchestrator."""
    
    def __init__(self, project_root: str = ".", dry_run: bool = False, create_backup: bool = True):
        self.project_root = project_root
        self.dry_run = dry_run
        self.create_backup = create_backup
        
        # Initialize components
        self.deployment_manager = DeploymentManager(project_root, dry_run, create_backup)
        self.content_generators = ContentGenerators()
        self.validation_runner = ValidationRunner(project_root)
    
    def deploy_all(self) -> dict:
        """Deploy all fixes and configurations."""
        print("🚀 StreamlineVPN Deployment Script (Refactored)")
        print("=" * 60)
        
        if self.dry_run:
            print("🔍 DRY RUN MODE - No files will be modified")
        
        # Generate and write all content files
        self._generate_all_content()
        
        # Apply deployment fixes
        deployment_result = self.deployment_manager.deploy_all_fixes()
        
        # Run validation
        validation_result = self.validation_runner.run_final_validation()
        
        return {
            "deployment": deployment_result,
            "validation": validation_result,
            "dry_run": self.dry_run
        }
    
    def _generate_all_content(self):
        """Generate all content files."""
        print("\n📝 Generating content files...")
        
        content_files = {
            "run_unified.py": self.content_generators.get_run_unified_content(),
            "run_api.py": self.content_generators.get_run_api_content(),
            "run_web.py": self.content_generators.get_run_web_content(),
            "src/streamline_vpn/web/static/js/main.js": self.content_generators.get_main_js_content(),
            "config/sources.yaml": self.content_generators.get_sources_yaml_content(),
            ".env.example": self.content_generators.get_env_example_content(),
            "pyproject.toml": self.content_generators.get_pyproject_toml_content(),
            "requirements.txt": self.content_generators.get_requirements_content(),
            "requirements-dev.txt": self.content_generators.get_requirements_dev_content(),
        }
        
        for file_path, content in content_files.items():
            success = self.deployment_manager.write_file(file_path, content)
            if success:
                print(f"✅ Generated: {file_path}")
            else:
                print(f"❌ Failed to generate: {file_path}")
    
    def run_tests(self) -> dict:
        """Run the test suite."""
        return self.validation_runner.run_tests()
    
    def run_coverage(self) -> dict:
        """Run coverage analysis."""
        return self.validation_runner.run_coverage_check()
    
    def get_operations_log(self) -> list:
        """Get the log of operations performed."""
        return self.deployment_manager.get_operations_log()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="StreamlineVPN Deployment Script")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode (no changes)")
    parser.add_argument("--no-backup", action="store_true", help="Skip backup creation")
    parser.add_argument("--run-tests", action="store_true", help="Run tests after deployment")
    parser.add_argument("--run-coverage", action="store_true", help="Run coverage after deployment")
    parser.add_argument("--output", help="Output file for results (JSON)")
    
    args = parser.parse_args()
    
    # Create deployer
    deployer = StreamlineVPNDeployer(
        project_root=args.project_root,
        dry_run=args.dry_run,
        create_backup=not args.no_backup
    )
    
    # Deploy all fixes
    results = deployer.deploy_all()
    
    # Run additional checks if requested
    if args.run_tests:
        print("\n🧪 Running tests...")
        test_results = deployer.run_tests()
        results["tests"] = test_results
    
    if args.run_coverage:
        print("\n📊 Running coverage...")
        coverage_results = deployer.run_coverage()
        results["coverage"] = coverage_results
    
    # Save results if requested
    if args.output:
        import json
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📄 Results saved to {args.output}")
    
    # Display summary
    print("\n" + "=" * 60)
    print("📊 DEPLOYMENT SUMMARY")
    print("=" * 60)
    
    deployment = results.get("deployment", {})
    validation = results.get("validation", {})
    
    print(f"Deployment Status: {deployment.get('status', 'unknown')}")
    print(f"Operations Performed: {deployment.get('operations_count', 0)}")
    print(f"Backup Created: {deployment.get('backup_created', False)}")
    
    if validation:
        print(f"Validation Status: {validation.get('overall_status', 'unknown')}")
        print(f"Python Syntax: {'✅' if validation.get('python_syntax') else '❌'}")
        print(f"Imports: {'✅' if validation.get('imports') else '❌'}")
        print(f"Configurations: {'✅' if validation.get('configurations') else '❌'}")
        print(f"File Completeness: {'✅' if validation.get('file_completeness') else '❌'}")
    
    if args.run_tests and "tests" in results:
        test_results = results["tests"]
        print(f"Tests: {'✅' if test_results.get('success') else '❌'}")
    
    if args.run_coverage and "coverage" in results:
        coverage_results = results["coverage"]
        print(f"Coverage: {'✅' if coverage_results.get('success') else '❌'}")
    
    print("=" * 60)
    
    # Determine exit code
    if deployment.get('status') == 'error':
        return 1
    elif validation.get('overall_status') == 'failed':
        return 1
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())

