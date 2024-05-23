import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setuptools.setup(
    name="dati_playground",
    version="0.0.1rc4",
    author="Roberto Polli",
    author_email="robipolli@gmail.com",
    description="Tools to manage and validate semantic assets.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ioggstream/json-semantic-playground",
    packages=setuptools.find_packages(),
    install_requires=requirements,
    include_package_data=True,
    package_data={"": ["data/*.yaml"]},
    keywords=["openapi", "rest", "semantic", "ontology", "json-ld"],
    classifiers=[
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
