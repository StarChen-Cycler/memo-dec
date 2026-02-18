"""
Setup script for memo-dec
"""

from setuptools import setup, find_packages

setup(
    name="memo-dec",
    version="0.1.0",
    author="Memo-Dec",
    description="AI Codebase Context Assistant - helps AI agents understand codebases",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=[
        "tree-sitter>=0.21.0",
        "tree-sitter-python>=0.20.0",
        "tree-sitter-javascript>=0.20.0",
        "tree-sitter-typescript>=0.20.0",
        "tree-sitter-c>=0.20.0",
        "tree-sitter-java>=0.20.0",
        "tree-sitter-markdown>=0.3.2",
        "tree-sitter-html>=0.19.0",
        "tree-sitter-json>=0.20.0",
        "tree-sitter-embedded-template>=0.20.0",
        # Additional language support (versions adjusted to match PyPI availability)
        "tree-sitter-go>=0.20.0",
        "tree-sitter-rust>=0.21.0",
        "tree-sitter-ruby>=0.21.0",
        "tree-sitter-php>=0.20.0",
        "tree-sitter-c-sharp>=0.21.0",
        "tree-sitter-kotlin>=1.0.0",
        "tree-sitter-swift>=0.0.1",
        "tree-sitter-scala>=0.23.0",
        "tree-sitter-bash>=0.21.0",
        "tree-sitter-yaml>=0.6.0",
        "tree-sitter-toml>=0.6.0",
        "tree-sitter-sql>=0.3.5",
        "openai>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "memo-dec=memo_dec.cli:main",
        ],
    },
)
