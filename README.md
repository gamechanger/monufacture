# Monufacture

Monufacture is a simple test data factory framework for Python which aims to make it easy to setup and teardown predictable test data in Mongo as part of testing functional code. 


# Installation

Install via easy_install:
```
easy_install monufacture
```
Or, via pip:
```
pip install monufacture
```

# Getting Started

More docs to come. For now - here's an example:

## Example

To illustrate how to use Monufacture, let's imagine a dull application which uses MongoDB to power a blogging site. 

We can declare reusable factories, indicating how to build valid documents of given types, using inline helper functions to inject dynamic content:

```python
from monufacture import factory, random_text, id_of, dependent, insert

factory("name", 
    first = random_text(),
    last = random_text()    
)

factory("user", db.data.user, # providing a PyMongo collection enables saving
    name = insert("name"),
    email = dependent(lambda doc: "%s.%s@test.com" % (doc['name']['first'], doc['name']['last']))
)

factory("blogpost", db.data.blogpost, 
    author = id_of("user")
    subject = random_text(250, spaces=True)
    text = random_text(2000, spaces=True)
    posted_date = lambda: Date()
    permalink = sequence(lambda n: "http://mysite.com/%s" % n)
)
```

With these factories registered, we can then use them to generate and automatically teardown test data during testing:

```python
from unittest import TestCase
from monufacture import build, build_list, create, create_list

class BloggingTestCase(TestCase):
    def __init__(self, *args, **kwargs):
        super(TestCase, self).__init__(*args, **kwargs)
        enable_factories(self) # ensures cleanup happens

    def test_some_functionality(self):
        # Create a valid blogpost and its dependencies in the DB
        blogpost = create("blogpost") 
        
        # Now test some stuff with the blogpost object...


    def test_some_other_functionality(self):
        # Builds a new blogpost object without saving it.
        blogpost = build("blogpost") 
        
        # ...


    def test_even_more(self):
        # Creates 5 blogposts
        blogposts = create_list("blogpost", 5)
        
        # ...


    def test_other_stuff(self):
        # Override default factory-generated values
        blogpost = create("blogpost", subject="How I learnt to love Python")

    # ...
```