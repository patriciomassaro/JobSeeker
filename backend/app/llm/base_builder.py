import os
import subprocess
from typing import Any


class BasePDFBuilder:
    def __init__(self):
        pass

    def _escape_latex(self, string: str) -> str:
        latex_special_chars = {
            "&": r"\&",
            "%": r"\%",
            "$": r"\$",
            "#": r"\#",
            "_": r"\_",
            "{": r"\{",
            "}": r"\}",
            "~": r"\textasciitilde{}",
            "^": r"\^{}",
            "\\": r"\textbackslash{}",
        }
        return "".join(latex_special_chars.get(c, c) for c in string)

    @staticmethod
    def _load_template(latex_path) -> str:
        with open(latex_path) as file:
            return file.read()

    def _replace_placeholders(self, latex_content: str, data: dict[str, Any]) -> str:
        for key, value in data.items():
            latex_content = latex_content.replace(key, value)
        return latex_content

    def generate_pdf(self, latex_content: str, output_path: str) -> bytes:
        with open(output_path + ".tex", "w") as f:
            f.write(latex_content)

        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", output_path + ".tex"],
            cwd=os.path.dirname(output_path),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        with open(output_path + ".pdf", "rb") as f:
            pdf_bytes = f.read()

        # Clean up temporary files
        for ext in [".aux", ".log", ".out", ".tex"]:
            if os.path.exists(output_path + ext):
                os.remove(output_path + ext)

        return pdf_bytes
