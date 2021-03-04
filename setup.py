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
        "grpclib>=0.4.1",
        "PyYAML>=5.4.1",
        "pytest>6.2",
        "vcrpy@git+https://github.com/gosuai/vcrpy.git@51e451783078964e1cbc5cc24864ac0c6a8333fd",
        "google-gosu@git+https://github.com/gosuai/gosu-grpc.git@45cd671bd92dbae7aae0bf7b1ff91825c8c55574",
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
