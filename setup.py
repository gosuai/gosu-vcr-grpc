import setuptools

setuptools.setup(
    name="gosu-vcr-grpc",
    packages=["gosu_vcr_grpc"],
    version="0.1.2",
    license="MIT",
    description="Pytest plugin to record grpc streams in cassettes",
    authors=[
        "Nikolay Bryskin <nb@gosu.ai>",
        "Slavik Greshilov <sg@gosu.ai",
    ],
    url="https://github.com/gosuai/gosu-vcr-grpc",
    keywords=["grpc", "vcr", "gosu"],
    install_requires=[
        "grpclib",
        "PyYAML",
        "pytest",
        "vcrpy",
        "google-gosu",
    ],
    classifiers=[
        "Development Status :: Production",
        "Intended Audience :: Gosu Fellows",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
    ],
    entry_points={
        "pytest11": [
            "vcr_grpc = gosu_vcr_grpc",
        ],
    },
)
