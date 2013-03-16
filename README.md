# Monufacture

Monufacture is a simple test data factory framework for Python which aims to make it as easy as possible to setup and teardown predictable test data in Mongo as part of testing functional code. 

The API borrows heavily from Thoughtbot's excellent [factory_girl](https://github.com/thoughtbot/factory_girl) gem for Ruby.

[![build status](https://travis-ci.org/tleach/monufacture.png?branch=master "Build status")](https://travis-ci.org/tleach/monufacture)

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

To illustrate how to use Monufacture, let's imagine some dull application which uses MongoDB to power a blogging site. We want to test our site's pages to ensure that when we attempt to get a given page it loads the right data, when we attempt to save a new blog post the database is updated, etc. You get the idea.

In order to perform this sort of testing, we usually need some suitable test data in the database in order to run a test. Monufacture helps you do this. Its API provides two related capabilities:

1. The ability to declare, in a nice, readable format, how to construct test documents. 
2. The ability to use these declared factories to effortlessly generate as many test documents as you need for your test.


Going back to our blogging application, let's image our database is pretty simple and has two collections: `user`, which holds user account information, and `blogpost` which contains all the data associated with a given post. 

If we wanted to use Monufacture to generate test data for this application, we'd start off by declaring factories something like this:

```python
trait("timestamped", {          # Traits can be used to declare commonly 
    "created":  ago(days=1),    # used document content which we want to mix
    "modified": date()          # into other documents.
})

with factory("user", db.users): # Declare a factory, providing a name and a Mongo collection object

    default({                   # Declare the default document for a factory
        "name":     {
            "first":    "John",
            "last":     "Smith"
        },
        "email":    dependent(lambda user: "{}.{}@test.com".format(     # The "dependent" helper lets us
                        user['name']['first'],                          # set field values from other
                        user['name']['last'])),                         # field values.
        "password": "abc123",
    }, traits=["timestamped"])

    document("admin", {         # In addition to the default factory we can declare
        "is_admin": True        # additional named factories for special cases.
    }, parent="default")        # We can also inherit from the default.


with factory("blogpost", db.blogpost):

    default({
        "author":       id_of("user"),                          # Using id_of we can insert the id of another document
        "subject":      random_text(length=100, spaces=True),   # We can generate random text to populate fields
        "content":      random_text(length=1000, spaces=True),
        "published":    ago(minutes=30),                        # We can generate a relative datetime
    }, traits=["timestamped"])

    fragment("comment", {       # We can declare reusable document fragments to be inserted into documents
        "commenter":    {
            "name":         random_text(spaces=True),
            "email":        sequence(lambda n: "commenter{}@test.com".format(n)),
            "text":         random_text(length=200)
        }
    })

    document("with_comments", {
        "comments":     list_of(embed("comment"), 10)   # Insert a list of 10 comment fragments
    }, parent="default")
```

With these factories registered, we can then use them to generate and automatically teardown test data during testing:

```python
class BloggingTestCase(TestCase):

    def test_get(self):
        # Create a valid blogpost and its dependencies in the DB
        blogpost = create("blogpost") 
        
        # Now we can test our application GET method
        response = app.get("/blogposts/{}".format(blogpost["_id"]))
        self.assertEquals(response.code, 200)
        self.assertEquals(response.body['subject'], blogpost['subject'])
        


    def test_create(self):
        # Builds a new blogpost documents without saving it.
        # Here we're using the named "with_comments" document
        new_post = build("blogpost", "with_comments") 
        
        # Test our application POST method saves the new document
        response = app.post("/blogposts", new_post)
        self.assertEquals(response.code, 201)
        self.assertNotNone(db.blogpost.find_one(response.body['_id']))


    def test_index(self):
        # Creates 5 blogposts in the database
        blogposts = create_list(5, "blogpost")
        
        # Test we can get all of them
        response = app.get('/blogposts')
        self.assertEquals(response.code, 200)
        self.assertEquals(len(response.body), 5)


    def test_other_stuff(self):
        # Override default factory-generated values
        blogpost = create("blogpost", subject="How I learnt to love Python")

        # Test we can get a post by subject
        response = app.get('/blogposts?subject={}'.format(
            urlencode("How I learnt to love Python")))
        self.assertEquals(response.code, 200)
        self.assertEquals(response.body['_id'], blogpost['_id'])
    

    def tearDown(self):
        # Clean up any test documents we created in the database after each test
        cleanup()
```

# API Reference

## Factory Declaration

### Factories

### Documents

### Traits

### Fragments

### Inheritance

### Helpers

#### sequence(fn)

Defines a sequential value for a factory attribute. On each successive invocation of this helper (i.e. when a new instance of a document is created by the enclosing factory) the given function is passed a sequentially incrementing number which should be used to return a dynamic value to be used on the model instance.

#### dependent(fn)

#### id_of(factory, [document])

#### random_text([[[[[[length], spaces], digits], upper], lower], other_chars])

#### dbref_to(factory, [type])

#### date([[[[[[[year], month], day], hour], minute], second], microsecond])

#### ago([[[[[[[years], months], days], hours], minutes], seconds], microseconds])

#### from_now([[[[[[[years], months], days], hours], minutes], seconds], microseconds])

#### list_of(fn, length)

#### object_id()

#### union(*fns)

#### one_of

### Writing Custom Helpers

## Factory Usage

### Building Documents

### Creating Documents

### Cleanup