import setuptools

setuptools.setup(
    name="Monufacture",
    version="0.2.6",
    author="Tom Leach",
    author_email="tom@leach.it",
    description="A lightweight factory framework for creating / tearing " +
                "down test data in MongoDB",
    license="BSD",
    keywords="mongo mongodb database testing factory pymongo",
    url="http://github.com/tleach/monufacture",
    packages=["monufacture"],
    long_description="Monufacture is a factory framework for creating test " +
                     "data in MongoDB, inspired by factory_girl.",
    install_requires=['pymongo'],
    tests_require=['mock', 'nose', 'freezegun']
)
