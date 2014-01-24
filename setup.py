import setuptools

setuptools.setup(
    name="Monufacture",
    version="0.3.0",
    author="Tom Leach",
    author_email="tom@gc.io",
    description="A lightweight factory framework for easily generating test data in MongoDB",
    license="BSD",
    keywords="mongo mongodb database testing factory pymongo",
    url="http://github.com/gamechanger/monufacture",
    packages=["monufacture"],
    long_description="Monufacture is a factory framework with an API designed to make " +
                     "it as easy as possible to generate valid test data in MongoDB. " +
                     "Inspired by the excellent factory_girl Ruby Gem.",
    install_requires=['pymongo'],
    tests_require=['mock', 'nose', 'freezegun', 'pytz']
)
