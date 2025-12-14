from setuptools import setup, find_packages

setup(
    name="botuvic",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click>=8.1.0",
        "python-dotenv>=1.0.0",
        "openai>=1.12.0",
        "anthropic>=0.34.0",
        "google-generativeai>=0.8.0",
        "rich>=13.7.0",
        "pydantic>=2.6.0",
        "requests>=2.31.0",
        "gitpython>=3.1.0",
        "pathspec>=0.12.0",
        "questionary>=2.0.0",
        "prompt-toolkit>=3.0.0",
        "pygments>=2.17.0",
    ],
    entry_points={
        "console_scripts": [
            "botuvic=botuvic.main_interactive:cli",
            "botuvic-simple=botuvic.main:cli",
        ],
    },
    python_requires=">=3.8",
)

