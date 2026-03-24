"""
PatchGuard CLI — Autonomous Security Remediation Agent.
Provides a unified interface for ingesting, classifying, and fixing security vulnerabilities.
"""
import argparse
import sys
import os
from pathlib import Path
from typing import List, Optional

from patchguard.parsers.sonarqube.parser import SonarQubeParser
from patchguard.parsers.mend.parser import MendParser
from patchguard.parsers.trivy.parser import TrivyParser
from patchguard.utils.severity import SeverityFilter
from patchguard.models.finding import Finding
from patchguard.generators.fix_generator import FixGenerator
from patchguard.generators.llm_client import LLMClient
from patchguard.validators.linter_validator import LinterValidator
from patchguard.retrievers.context_retriever import ContextRetriever


def get_parser(tool: str):
    """Get the appropriate parser for the tool."""
    if tool == "sonarqube":
        return SonarQubeParser()
    elif tool == "mend":
        return MendParser()
    elif tool == "trivy":
        return TrivyParser()
    else:
        raise ValueError(f"Unsupported tool: {tool}")


def main():
    parser = argparse.ArgumentParser(
        description="PatchGuard — Autonomous Security Remediation Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan a SonarQube report and show findings
  python -m patchguard scan --tool sonarqube --input sonarqube_scan.json

  # Fix high-severity vulnerabilities in a Trivy report using OpenAI
  $env:OPENAI_API_KEY="sk-..."
  python -m patchguard fix --tool trivy --input trivy_scan.json --repo ./my-project --provider openai

  # Pass API key directly as an argument
  python -m patchguard fix --tool sonarqube --input scan.json --repo ./ --provider anthropic --api-key "ant-..."
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # 'scan' command
    scan_parser = subparsers.add_parser("scan", help="Scan and list findings from a report")
    scan_parser.add_argument("--tool", required=True, choices=["sonarqube", "mend", "trivy"], help="Security tool source")
    scan_parser.add_argument("--input", required=True, help="Path to the JSON scan report")
    scan_parser.add_argument("--severity", nargs="+", help="Severity levels to include (e.g. CRITICAL HIGH)")

    # 'fix' command
    fix_parser = subparsers.add_parser("fix", help="Generate and apply fixes for findings")
    fix_parser.add_argument("--tool", required=True, choices=["sonarqube", "mend", "trivy"], help="Security tool source")
    fix_parser.add_argument("--input", required=True, help="Path to the JSON scan report")
    fix_parser.add_argument("--repo", required=True, help="Path to the repository to fix")
    fix_parser.add_argument("--severity", nargs="+", help="Severity levels to include")
    fix_parser.add_argument("--provider", default="mock", choices=["openai", "anthropic", "mock"], help="LLM provider")
    fix_parser.add_argument("--model", help="LLM model name (defaults based on provider)")
    fix_parser.add_argument("--api-key", help="LLM API key (or set OPENAI_API_KEY/ANTHROPIC_API_KEY env vars)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        # Load and parse findings
        if not os.path.exists(args.input):
            print(f"Error: Input file '{args.input}' not found.")
            sys.exit(1)

        with open(args.input, "r") as f:
            raw_data = f.read()

        tool_parser = get_parser(args.tool)
        findings = tool_parser.parse(raw_data)

        # Apply severity filtering
        severity_filter = SeverityFilter()
        
        # Convert string severities to Severity enum if provided
        custom_severities = None
        if args.severity:
            from patchguard.models.finding import Severity
            custom_severities = []
            for s in args.severity:
                try:
                    custom_severities.append(Severity(s.upper()))
                except ValueError:
                    print(f"Warning: Invalid severity level '{s}', skipping.")
        
        filtered_findings = severity_filter.filter(findings, args.tool, custom_severities)

        if args.command == "scan":
            print(f"\n[+] Found {len(filtered_findings)} {args.tool} findings (filtered by {args.severity or 'defaults'}):")
            print("-" * 80)
            for finding in filtered_findings:
                print(f"ID: {finding.finding_id:<20} Sev: {finding.severity.value:<10} File: {finding.file_path}")
                print(f"Message: {finding.message}")
                if finding.fix_hint:
                    print(f"Fix Hint: {finding.fix_hint}")
                print("-" * 80)

        elif args.command == "fix":
            print(f"\n[*] Starting remediation for {len(filtered_findings)} findings...")
            
            # Default models if not specified
            model = args.model
            if not model:
                if args.provider == "openai":
                    model = "gpt-4o"
                elif args.provider == "anthropic":
                    model = "claude-3-5-sonnet-20241022"
                else:
                    model = "mock-model"

            # Initialize components for fixing
            llm_client = LLMClient(provider=args.provider, model=model, api_key=args.api_key)
            validator = LinterValidator()
            fix_generator = FixGenerator(llm_client, validator)
            context_retriever = ContextRetriever(args.repo)

            results = []
            for finding in filtered_findings:
                print(f"\n[>] Processing {finding.finding_id} ({finding.file_path})...")
                
                # Retrieve context
                try:
                    context = context_retriever.retrieve(finding)
                    if not context:
                        print(f"    [!] Error: Could not retrieve code context for {finding.file_path}")
                        continue
                except Exception as e:
                    print(f"    [!] Context error: {str(e)}")
                    continue

                # Generate fix
                try:
                    fix_result = fix_generator.generate(finding, context)
                    results.append(fix_result)

                    if fix_result.success:
                        if fix_result.attempts == 0:
                            print(f"    [i] Skipped: {fix_result.error_message}")
                        else:
                            print(f"    [+] Fix generated successfully in {fix_result.attempts} attempts!")
                            print(f"    [+] Validation: {fix_result.linter_output or 'Passed'}")
                    else:
                        print(f"    [-] Failed: {fix_result.error_message}")
                except Exception as e:
                    print(f"    [!] Fix generation error: {str(e)}")

            # Summary
            success_count = sum(1 for r in results if r.success and r.attempts > 0)
            skipped_count = sum(1 for r in results if r.success and r.attempts == 0)
            failed_count = sum(1 for r in results if not r.success)
            
            print(f"\n{'='*40}")
            print(f"Remediation Summary")
            print(f"{'='*40}")
            print(f"Successfully fixed:  {success_count}")
            print(f"Skipped (manual):    {skipped_count}")
            print(f"Failed to fix:       {failed_count}")
            print(f"Total processed:     {len(results)}")
            print(f"{'='*40}\n")

    except Exception as e:
        print(f"Fatal Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
