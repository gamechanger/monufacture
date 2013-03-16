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
trait("timestamped", {                                              # Traits can be used to declare commonly 
    "created":  ago(days=1),                                        # used document content which we want to mix
    "modified": date()                                              # into other documents.
})

with factory("user", db.users):                                     # Declare a factory, providing a name and a Mongo collection object

    default({                                                       # Declare the default document for a factory
        "first_name":   "John",
        "last_name":    "Smith"
        "email":    dependent(lambda u: "{}.{}@test.com".format(    # The "dependent" helper lets us
                                            u['first_name'],        # set field values from other
                                            u['last_name'])),       # field values.
        "password": "abc123",
    }, traits=["timestamped"])

    document("admin", {                                             # In addition to the default factory we can declare
        "is_admin": True                                            # additional named factories for special cases.
    }, parent="default")                                            # We can also inherit from the default.


with factory("blogpost", db.blogpost):

    default({
        "author":       id_of("user"),                              # Using id_of we can insert the id of another document
        "subject":      random_text(length=100, spaces=True),       # We can generate random text to populate fields
        "content":      random_text(length=1000, spaces=True),
        "published":    ago(minutes=30),                            # We can generate a relative datetime
    }, traits=["timestamped"])

    fragment("comment", {                                           # We can declare reusable document fragments to be inserted into documents
        "commenter":    {
            "name":         random_text(spaces=True),
            "email":        sequence(lambda n: "commenter{}@test.com".format(n)),
            "text":         random_text(length=200)
        }
    })

    document("with_comments", {
        "comments":     list_of(embed("comment"), 10)               # Insert a list of 10 comment fragments
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

Factories are declared by calling the `monufacture.factory()` method using a `with` block. 

Each factory must be given a name and be provided with a PyMongo collection object which it will use to insert documents it creates.

Inside the factory's `with` block, the structure and attributes of the documents it will generate are declared using the `default`, `document`, `trait` and `fragment` methods (described in more detail below):
```python
with factory("vehicle", db.vehicles):   # All documents will be written to the "vehicles" collection in MongoDB.
    trait("car", {
        "wheels":       4
    })

    trait("bike", {
        "wheels":       2
    })

    trait("new", {
        "is_new":       True
        "purchased":    date()
    })

    trait("used", {
        "is_new":       False
        "num_owners":   2
        "purchased":    ago(years=1)
        "history":      list_of(embed("service_record"), 3)
    })

    fragment("service_record", {
        "date":         ago(months=3)
        "repairs":      random_text(length=500, spaces=True)
    })

    default({
        "model":        random_text(spaces=True)
        "price":        1234.56
    })

    document("new_bmw_motorbike", {
        "make":         "BMW"
    }, parent="default", traits=["new", "bike"])

    document("used_jaguar_car", {
        "make":         "Jaguar"
    }, parent="default", traits=["used", "car"])
```

### Documents

Documents are declared within factories and are ultimately what factories build. Any number of named document structures may declared within a single factory (e.g. to test different scenarios) but all declared documents must be valid for Mongo collection associated with the factory. 

To declare a document, use the `document` method inside an enclosing `factory` declaration:
```python
with factory("vehicle", db.vehicles):
    document("ford", {
        "make":     "Ford",
        "model":    "Taurus"
    })
```
The above example declares a static document which when generated (see "Using Factories") will always contain the same two fields with the same values.

To make things a bit more interesting, Monufacture provides inline helper functions (see "Helpers") which can be used to dynamically generate field values:
```python
with factory("vehicle", db.vehicles):
    document("ford", {
        "make":     "Ford",
        "model":    random_text()
    })
```
The above example factory would generate a different value for the `"model"` field each time a document is generated.

#### The "default()" document

Within each factory, a single "default" document structure should be declared. This is usually the simplest, most generic version of a document which is likely to be useful in most test contexts:
```python
with factory("vehicle", db.vehicles):
    default({
        "make":     random_text(),
        "model":    random_text()
    })
```

### Inheritance
When declaring multiple flavours of a document in a factory, it's common to want to reuse a base document structure in many documents. For this, Monufacture allows document declarations to inherit from one another making this process nice and DRY.
```python
with factory("vehicle", db.vehicles):
    default({
        "cc":       random_number(min=500, max=3000)
    })

    document("car", {
        "wheels":   4
    }, parent="default")        # Inherits fields from the default document

    document("bike", {
        "wheels":   2
    }, parent="default")        # Inherits fields from the default document

    document("mazda", {
        "make":     "Mazda"
    }, parent="car")            # Inherits from the "car" and default documents

    document("mazda_mx5", {
        "model":    "MX-5"
    }, parent="mazda")          # Inherits from the "mazda", car" and default documents
```
Note:
 - If a document redeclares a field already declared in a parent document, the child document's value wins.
 - Inheritance only works within the scope of a single factory. Cross-factory inheritance is not supported.

### Traits
Traits allow common sets field values to be declared separately and then "mixed in" to as many document declarations as needed. 

Traits may be declared globally so that they may be used within all factories, or scoped inside just one factory.

```python
# Declare a global "timestamped" trait which can be used in any factory
trait("timestamped", {
    "created":      ago(weeks=2),
    "modified":     ago(minutes=1)
})

with factory("vehicle", db.vehicles):
    
    # Declare some reusable traits 
    trait("honda", {"make": "Honda"})
    trait("bmw", {"make": "BMW"})
    trait("bike", {"wheels": 2})
    trait("car", {"wheels": 4})m

    # Declare various documents by mixing up combinations of traits
    document("bmw_bike", traits=["bmw", "bike", "timestamped"])
    document("honda_bike", traits=["honda", "bike", "timestamped"])
    document("bmw_car", traits=["bmw", "car", "timestamped"])
    document("honda_car", traits=["honda", "car", "timestamped"])

with factory("customer", db.customers):
    default({
        "name":     random_text(),
        "address:   {
            "line_1":   random_text(),
            "line_2":   random_text(),
            "zip":      random_text(digits=True, length=5)
        }
    }, traits=["timestamped"])  # "timestamped" trait used in multiple places
```
Note:
 - In the event a trait and the document referring to that trait declare the same field, the document's definition takes precedence.

### Fragments
Fragments are a bit like traits in that they allow reusable, well, fragments to be declared separately and then included in multiple document declarations. However, whereas traits get "mixed in" to a document, fragments are designed to be embedded into a document at a certain insertion point using the `embed` function.

```python
with factory("vehicle", db.vehicles):
    # Declare an "owner" fragment we can use in multiple places
    fragment("owner", {
        "name":             random_text(),
        "purchased":        ago(weeks=random_number(max=200))
    })

    # Now declare a document where we use the "owner" fragment to
    # embed details of a current owner and a list of previous owners.
    default({
        "make":             random_text(),
        "model":            random_text(),
        "current_owner":    embed("owner", purchased=date())
        "previous_owners":  list_of(embed("owner"), 3)
    })
```

Fragments may be used inside traits:
```python
with factory("vehicle", db.vehicles):
    # Declare an "owner" fragment we can use in multiple places
    fragment("owner", {
        "name":             random_text(),
        "purchased":        ago(weeks=random_number(max=200))
    })

    trait("preowned", {
        "previous_owners":  list_of(embed("owner"), 3)
    })

    # Now declare a document where we use the "owner" fragment to
    # embed details of a current owner and a list of previous owners.
    default({
        "make":             random_text(),
        "model":            random_text(),
        "current_owner":    embed("owner", purchased=date())
    }, traits=["preowned"])
```

Fragments also support inheritance in the same manner as documents:
```python
with factory("vehicle", db.vehicles):
    fragment("identity", {
        "id":               object_id()
    })

    # Declare an "owner" fragment we can use in multiple places
    fragment("owner", {
        "name":             random_text(),
        "purchased":        ago(weeks=random_number(max=200))
    }, parent="identity")

```

Notes:
 - Fragments must be declared inside the scope of a `with factory():` block. Global fragments are not supported.

### Helpers

Helpers are useful placeholder functions which can be used to insert generated data into documents at _build time_.

At their most basic level, helpers allow you to generate simple primitive values for fields (e.g. `random_text`). However, some of the more sophisticated helpers allow to you declare large document structures and satisfy dependencies between collections with the minimum of effort.


#### sequence(fn)

Defines a sequential value for a factory attribute. On each successive invocation of this helper (i.e. when a new instance of a document is created by the enclosing factory) the given function is passed a sequentially incrementing number which should be used to return a dynamic value to be used on the model instance.

##### Arguments
| `fn(n)` | A function/lambda which returns a value based on the given sequence value. |

##### Example
```python
# Generate a unique email address for each created user.
document("user", {
    "email": sequence(lambda n: "user{}@test.com".format(n))
})
```

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