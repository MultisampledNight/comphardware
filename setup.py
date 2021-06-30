import setuptools

with open("README.md", encoding="utf-8") as fh:
    long_description = fh.read() 

setuptools.setup(
    name="comphardware",
    version="0.1.1",
    license="Apache-2",
    url="https://github.com/MultisampledNight/comphardware",

    author="MultisampledNight",
    author_email="contact@multisamplednight.com",

    description="Library for comparing hardware",
    long_description=long_description,
    long_description_content_type="text/markdown",

    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: System :: Hardware",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS :: MacOS X",
    ],
    python_requires=">=3.8",
    install_requires=[
        "bs4",
        "pandas",
        "psutil",
        "requests",
        "PyOpenGL",
        "setuptools",
    ],

    include_package_data=True,
)
