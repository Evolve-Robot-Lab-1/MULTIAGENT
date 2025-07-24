from setuptools import setup, find_packages

setup(
    name="browser-use",
    version="0.1.44",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.10",
    install_requires=[
        "anyio>=4.9.0",
        "httpx>=0.27.2",
        "pydantic>=2.10.4,<2.11.0",
        "python-dotenv>=1.0.1",
        "requests>=2.32.3",
        "posthog>=3.7.0",
        "patchright>=1.51.0",
        "markdownify==1.1.0",
        "langchain-core==0.3.49",
        "langchain-openai==0.3.11",
        "langchain-anthropic==0.3.3",
        "langchain-ollama==0.3.0",
        "langchain-google-genai==2.1.2",
        "langchain-deepseek>=0.1.3",
        "langchain>=0.3.21",
    ],
    package_data={
        'browser_use': ['**/*.js', '**/*.md'],
    }
)