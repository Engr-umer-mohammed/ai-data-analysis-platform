"""
setup.py – Packaging configuration for AI Data Analysis Agent
"""

import os
from setuptools import setup, find_packages

# ─── Read README.md (with fallback) ───────────────────────────────
try:
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = "AI-powered data analysis agent with domain customizations."

# ─── Read requirements.txt (with fallback) ────────────────────────
requirements = []
try:
    with open("requirements.txt", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                requirements.append(line)
except FileNotFoundError:
    requirements = [
        "pandas>=1.5.0",
        "numpy>=1.24.0",
        "matplotlib>=3.7.0",
        "seaborn>=0.12.0",
        "openpyxl>=3.1.0",
        "scipy>=1.10.0",
        "google-genai>=0.1.0",
        "python-dotenv>=1.0.0",
    ]

setup(
    name="ai-data-analysis-agent",
    version="1.0.0",
    author="Umer Mohamed",
    author_email="umermohammed62@gmail.com",
    description="AI-powered data analysis agent with domain customizations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ai-data-analysis-agent",
    packages=find_packages(
        exclude=["sample_data", "reports", "charts", "excel_reports", "output", "temp"]
    ),
    py_modules=["main", "dashboard"],  # ← Added dashboard
    include_package_data=True,
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "ai-agent = main:main",
            "ai-dashboard = dashboard:main",  # ← Added
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
)