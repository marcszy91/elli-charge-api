"""Setup configuration for elli-api-client package."""
from setuptools import setup, find_packages
from pathlib import Path

# Read the long description from README
this_directory = Path(__file__).parent
long_description = (this_directory / "src" / "elli_api_client" / "README.md").read_text(encoding="utf-8")

setup(
    name="elli-api-client",
    version="0.1.0",
    author="Marc Szymkowiak",
    description="Python client for Elli Charging API with OAuth2 PKCE authentication",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/elli-charge-api",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/elli-charge-api/issues",
        "Documentation": "https://github.com/yourusername/elli-charge-api#readme",
        "Source Code": "https://github.com/yourusername/elli-charge-api",
    },
    package_dir={"": "src"},
    packages=["elli_api_client"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.11",
    install_requires=[
        "httpx>=0.27.0",
        "pydantic>=2.9.0",
        "pydantic-settings>=2.5.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.1.1",
            "pytest-asyncio>=0.23.6",
            "black>=24.3.0",
            "isort>=5.13.2",
            "flake8>=7.0.0",
        ],
    },
    keywords="elli volkswagen charging wallbox api ev electric-vehicle",
)
