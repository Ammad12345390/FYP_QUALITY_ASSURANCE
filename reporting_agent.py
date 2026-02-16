"""
Reporting Agent for AI Test Generation System

Responsibilities:
- Parse unittest execution logs
- Extract test metrics (pass/fail/error)
- Analyze failures using LLM
- Generate Markdown & PDF test reports
"""

import re
from pathlib import Path
from fpdf import FPDF
from dotenv import load_dotenv
from openai import OpenAI
import matplotlib.pyplot as plt
import os
import time

load_dotenv()

class ReportingAgent:
    def __init__(self, log_path: str):
        self.log_path = Path(log_path)
        if not self.log_path.exists():
            raise FileNotFoundError(f"Log file not found: {log_path}")

        self.client = OpenAI()
        self.results = {}  # stores parsed log summary

    # --------------------------------------------------
    # STEP 1: Parse unittest log
    # --------------------------------------------------
    def parse_unittest_log(self) -> dict:
        content = self.log_path.read_text(encoding="utf-8", errors="ignore")

        # Basic summary dictionary
        self.results = {
            "tests_run": 0,
            "failures": 0,
            "errors": 0,
            "skipped": 0,
            "failed_tests": [],
            "error_tests": [],
            "raw_log": content,
            "status": "UNKNOWN",
            "recommendations": []
        }

        # Total tests
        match = re.search(r"Ran (\d+) tests?", content)
        if match:
            self.results["tests_run"] = int(match.group(1))

        # Failures & Errors
        self.results["failures"] = content.count("FAIL:")
        self.results["errors"] = content.count("ERROR:")

        # Failed test names
        self.results["failed_tests"] = re.findall(r"FAIL: (.+)", content)
        self.results["error_tests"] = re.findall(r"ERROR: (.+)", content)

        # Overall status
        if self.results["failures"] > 0 or self.results["errors"] > 0:
            self.results["status"] = "FAILED"
        else:
            self.results["status"] = "PASSED"

        # Default recommendations
        self.results["recommendations"] = [
            "Remove import-time side effects in main.py.",
            "Parameterize stdout/stderr streams for testability.",
            "Ensure exceptions propagate correctly (do not swallow).",
            "Refactor main.py to separate logic from IO.",
            "Add explicit output verification tests for stdout/stderr behavior.",
            "Add integration/CI checks to avoid import-time side effects."
        ]

        return self.results

    # --------------------------------------------------
    # STEP 2: AI-based Failure Analysis (optional)
    # --------------------------------------------------
    def analyze_with_llm(self, summary: dict) -> str:
        prompt = f"""
You are a Senior QA Automation Engineer.

Below is the result of an automated unittest execution.

Test Summary:
- Total Tests: {summary['tests_run']}
- Failures: {summary['failures']}
- Errors: {summary['errors']}

Failed Tests:
{summary['failed_tests']}

Error Tests:
{summary['error_tests']}

Raw Log:
{summary['raw_log']}

Your Tasks:
1. Identify root causes of failures and errors
2. Categorize issues (logic bug, import error, environment issue, missing mock, syntax issue)
3. Suggest concrete fixes
4. Assess overall code quality (score 1–10)
5. Recommend improvements for test coverage

Respond in clear, professional language.
"""

        response = self.client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {"role": "system", "content": "You are an expert QA engineer."},
                {"role": "user", "content": prompt},
            ],
        )

        return response.choices[0].message.content

    # --------------------------------------------------
    # STEP 2.5: Generate Charts
    # --------------------------------------------------
    def generate_charts(self, summary: dict) -> str:
        """
        Generates a pie chart for test results.
        Returns the path to the saved chart image.
        """
        labels = ['Passed', 'Failed', 'Errors']
        passed = summary['tests_run'] - summary['failures'] - summary['errors']
        sizes = [passed, summary['failures'], summary['errors']]
        colors = ['#4CAF50', '#FF5252', '#FFC107']  # Green, Red, Amber
        explode = (0.1, 0, 0)  # explode 1st slice

        plt.figure(figsize=(6, 6))
        plt.pie(sizes, explode=explode, labels=labels, colors=colors,
                autopct='%1.1f%%', shadow=True, startangle=140)
        plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        plt.title("Test Execution Summary")

        chart_path = "test_chart.png"
        plt.savefig(chart_path)
        plt.close()
        return chart_path

    # --------------------------------------------------
    # STEP 3: Generate Markdown Report
    # --------------------------------------------------
    def generate_markdown_report(self, summary: dict, ai_analysis: str = "") -> str:
        status = " PASSED" if summary["failures"] == 0 and summary["errors"] == 0 else " FAILED"

        report = f"""
# 🧪 AI Test Execution Report

## 📌 Overall Status
*{status}*

---

##  Test Summary
- *Total Tests Run:* {summary['tests_run']}
- *Failures:* {summary['failures']}
- *Errors:* {summary['errors']}

---

##  Failed Tests
{chr(10).join(summary['failed_tests']) if summary['failed_tests'] else "None"}

---

##  Error Tests
{chr(10).join(summary['error_tests']) if summary['error_tests'] else "None"}

---

##  AI Analysis & Recommendations
{ai_analysis or chr(10).join(summary.get('recommendations', []))}

---

## 🛠 Generated By
*AI-Powered Test Reporting Agent*
"""
        return report

    # --------------------------------------------------
    # STEP 4: Save Markdown Report
    # --------------------------------------------------
    def save_markdown_report(self, report_content: str, output_path: str = "test_report.md") -> Path:
        output_path = Path(output_path)
        output_path.write_text(report_content, encoding="utf-8")
        return output_path

    # --------------------------------------------------
    # STEP 5: Generate PDF Report
    # --------------------------------------------------
    # --------------------------------------------------
    # STEP 5: Generate PDF Report
    # --------------------------------------------------
    def generate_pdf_report(self, output_path: str = "test_report.pdf", coverage_report: str = ""):
        if not self.results:
            raise ValueError("No parsed results found. Run parse_unittest_log() first.")

        pdf = FPDF()
        pdf.add_page()
        
        # Colors
        PRIMARY_COLOR = (33, 150, 243)  # Blue
        SECONDARY_COLOR = (100, 100, 100) # Grey

        # Header
        pdf.set_font("Arial", 'B', 24)
        pdf.set_text_color(*PRIMARY_COLOR)
        pdf.cell(0, 15, "AI Test Execution Report", ln=True, align="C")
        pdf.ln(5)
        
        pdf.set_font("Arial", '', 10)
        pdf.set_text_color(*SECONDARY_COLOR)
        pdf.cell(0, 10, f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="C")
        pdf.ln(10)

        # Overall Status
        pdf.set_font("Arial", 'B', 16)
        status = self.results['status']
        if status == "PASSED":
             pdf.set_text_color(76, 175, 80) # Green
        else:
             pdf.set_text_color(244, 67, 54) # Red
             
        pdf.cell(0, 10, f"Overall Status: {status}", ln=True, align="C")
        pdf.set_text_color(0, 0, 0) # Reset to black

        # Chart
        try:
            chart_path = self.generate_charts(self.results)
            # Center the image
            pdf.image(chart_path, x=60, w=90) 
            os.remove(chart_path) # Cleanup
        except Exception as e:
            print(f"Error generating chart: {e}")

        # Test Summary
        pdf.ln(10)
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "  Test Summary", ln=True, fill=True)
        pdf.ln(2)
        
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 8, f"Total Tests Run: {self.results['tests_run']}", ln=True)
        pdf.cell(0, 8, f"Failures: {self.results['failures']}", ln=True)
        pdf.cell(0, 8, f"Errors: {self.results['errors']}", ln=True)

        # Coverage Section
        if coverage_report:
            pdf.ln(10)
            pdf.set_fill_color(240, 240, 240)
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, "  Code Coverage", ln=True, fill=True)
            pdf.ln(2)
            
            pdf.set_font("Courier", '', 10)
            # Split coverage report into lines
            for line in coverage_report.split('\n'):
                 pdf.cell(0, 5, line, ln=True)

        # Failures & Errors Section
        if self.results['failures'] > 0 or self.results['errors'] > 0:
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 14)
            pdf.set_text_color(244, 67, 54)
            pdf.cell(0, 10, "  Failures & Errors", ln=True)
            pdf.set_text_color(0, 0, 0)
            
            pdf.set_font("Arial", '', 11)
            
            if self.results['failed_tests']:
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 8, "Failed Tests:", ln=True)
                pdf.set_font("Arial", '', 11)
                for fail in self.results['failed_tests']:
                    pdf.multi_cell(0, 6, f"- {fail}")
                pdf.ln(2)

            if self.results['error_tests']:
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 8, "Error Tests:", ln=True)
                pdf.set_font("Arial", '', 11)
                for err in self.results['error_tests']:
                    pdf.multi_cell(0, 6, f"- {err}")

        # AI Analysis & Recommendations
        pdf.ln(10)
        pdf.set_fill_color(230, 240, 255) # Light blue
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "  AI Analysis & Recommendations", ln=True, fill=True)
        pdf.ln(2)
        
        pdf.set_font("Arial", '', 11)
        for rec in self.results.get('recommendations', []):
            pdf.multi_cell(0, 7, f"- {rec}")

        # Footer
        pdf.set_y(-20)
        pdf.set_font('Arial', 'I', 8)
        pdf.set_text_color(128)
        pdf.cell(0, 10, 'Page ' + str(pdf.page_no()), 0, 0, 'C')

        # Save PDF
        pdf.output(output_path)
        print(f"PDF generated successfully at {Path(output_path).resolve()}")

# --------------------------------------------------
# Standalone Execution (Optional)
# --------------------------------------------------
if __name__ == "__main__":
    log_file = input("Enter path to unittest log file: ").strip()

    agent = ReportingAgent(log_file)

    # Parse logs
    agent.parse_unittest_log()

    # Optional AI analysis
    # ai_analysis = agent.analyze_with_llm(agent.results)

    # Generate Markdown
    markdown_report = agent.generate_markdown_report(agent.results)
    md_path = agent.save_markdown_report(markdown_report)
    print(f"Markdown report saved at: {md_path.resolve()}")

    # Generate PDF
    agent.generate_pdf_report("ai_test_report.pdf")
