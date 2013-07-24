# Monufacture

Monufacture is a simple test data factory framework for Python which aims to make it as easy as possible to setup and teardown predictable test data in Mongo as part of testing functional code. 

The API borrows heavily from Thoughtbot's excellent [factory_girl](https://github.com/thoughtbot/factory_girl) gem for Ruby.

[![build status](https://travis-ci.org/gamechanger/monufacture.png?branch=master "Build status")](https://travis-ci.org/gamechanger/monufacture)

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
from monufacture import factory, trait, embed, fragment, document, default
from monugacture.helpers import date, ago, list_of, random_text


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
from monufacture import document, factory


with factory("vehicle", db.vehicles):
    document("ford", {
        "make":     "Ford",
        "model":    "Taurus"
    })
```
The above example declares a static document which when generated (see "Using Factories") will always contain the same two fields with the same values.

To make things a bit more interesting, Monufacture provides inline helper functions (see "Helpers") which can be used to dynamically generate field values:
```python
from monufacture import document, factory
from monufacture.helpers import random_text


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
from monufacture import default, factory
from monufacture.helpers import random_text


with factory("vehicle", db.vehicles):
    default({
        "make":     random_text(),
        "model":    random_text()
    })
```

### Inheritance
When declaring multiple flavours of a document in a factory, it's common to want to reuse a base document structure in many documents. For this, Monufacture allows document declarations to inherit from one another making this process nice and DRY.
```python
from monufacture import document, factory, default


with factory("vehicle", db.vehicles):
    default({
        "cc":       1500
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
from monufacture import trait, document, factory, default
from monufacture.helpers import ago, random_text


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
from monufacture import trait, document, factory, default, fragment, embed
from monufacture.helpers import ago, random_text, list_of


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
        "current_owner":    embed("owner")
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



## Helpers

Helpers are useful placeholder functions which can be used to insert generated data into documents at _build time_.

At their most basic level, helpers allow you to generate simple primitive values for fields (e.g. `random_text`). However, some of the more sophisticated helpers allow to you declare large document structures and satisfy dependencies between collections with the minimum of effort.

All helpers live in the `monufacture.helpers` module.

---

### `sequence([fn])`

Defines a sequential value for a document attribute. On each successive invocation of this helper (i.e. when a new instance of a document is created by the enclosing factory) the given function is passed a sequentially incrementing number which should be used to return a dynamic value to be used on the model instance.

When used without passing a function, this helper just inserts the raw sequence number into the document.

#### Arguments

| Argument | Description |
| -------- | ----------- |
| `fn(n)`  | A function/lambda which returns a value based on the given sequence value. *Optional* |

#### Example
```python
from monufacture.helpers import sequence


# Generate a unique email address for each created user.
document("user", {
    "email": sequence(lambda n: "user{}@test.com".format(n))
})
```

---

### `dependent(fn)`

Allows a dependent value to be dynamically generated from the value(s) of other attributes in the document. 

#### Arguments

| Argument | Description |
| -------- | ----------- |
| `fn(doc)` | A function/lambda which returns a value based on other value(s) found on the provided document node. The provided `doc` node is the node is the document on which the field being set lives. |

#### Example
```python
from monufacture.helpers import dependent


document("user", {
    "first":    "John",
    "last":     "Smith",
    "email":    dependent(lambda doc: "{}{}@test.com".format(doc['first'], doc['last']))
})
```
Tip: The document object passed to your generator function has a `head` attribute which refers back to the root of the document. This is particularly useful if you need to insert a dependent value, which refers to a non-sibling field, into a nested portion of your document.

---

### `id_of(factory, [document], **overrides)`

Creates a document in the database using the given factory (and optional document name) and then inserts the _id of the created document as the value of the referring field. This is a particularly effective way to effortlessly create a hierarchy of dependent documents for testing purposes. Simply declaring a document's dependency in this way will result in that dependency being created at build time. Yay!

You can also provide overrides to the document being created which can either be literals or functions evaluated on creation.

#### Arguments

| Argument | Description |
| -------- | ----------- |
| `factory`  | The name of the factory to use to create the depended-on document. | 
| `document` | The named document within the factory to create. If not provided the default document is created. *Optional* |
| `**overrides` | Override field values to be passed to the document being created. Values can be literals or functions. Functions are passed the current node (in a similar manner to the dependency helper) and must return a literal value.|

#### Example
```python
from monufacture.helpers import id_of, random_text, list_of


with factory("team", db.teams):
    default({
        "name":             random_text(),
        "players":          list_of(random_text(), 11)
    })


# When a "game" is created, we'll also create two teams and reference them by _id
with factory("game", db.games):
    default({
        "home_team_id":     id_of("team")
        "away_team_id":     id_of("team")
    })

# We could also provide an override for each team name as appropriate
with factory("game", db.games):
    default({
        "home_team_name":   text(),
        "away_team_name":   text(),
        "home_team_id":     id_of("team", name=lambda node: node['home_team_name'])
        "away_team_id":     id_of("team", name=lambda node: node['away_team_name'])
    })
```

---

### `dbref_to(factory, [document], **overrides)`

Very similar to the `id_of` helper, only the inserted reference to the created document is a MongoDB DBRef structure rather than just an _id. 

#### Arguments

| Argument | Description |
| -------- | ----------- |
| `factory`  | The name of the factory to use to create the depended-on document. | 
| `document` | The named document within the factory to create. If not provided the default document is created. *Optional* |

#### Example
```python
from monufacture.helpers import dbref_to, random_text, list_of


with factory("team", db.teams):
    default({
        "name":             random_text(),
        "players":          list_of(random_text(), 11)
    })


# When a "game" is created, we'll also create two teams and reference them by _id
with factory("game", db.games):
    default({
        "home_team":     dbref_to("team")
        "away_team":     dbref_to("team")
    })
```

---

### `random_text([[[[[[length], spaces], digits], upper], lower], other_chars])`

*Alias*: `text`

Inserts a random piece of text adhereing the provided criteria.

#### Arguments

| Argument | Description |
| -------- | ----------- |
| `length`      | The length of the string to return. *Default: 10*. *Optional* |
| `spaces`      | Include spaces? *Default: False*. *Optional* |
| `digits`      | Include numeric digits? *Default: False*. *Optional* |
| `upper`       | Include uppercase characters? *Default: True*. *Optional* |
| `lower`       | Include lowercase characters? *Default: True*. *Optional* |
| `other_chars` | A list of other characters to include (e.g. `[".", "?"]`). *Optional* |

#### Example
```python
from monufacture.helpers import random_text


document("blogpost", {
    "subject":  random_text(spaces=True, length=200),
    "content":  random_text(spaces=True, length=1000, other_chars=["."] 
})

```

---

### `random_number(max)`
### `random_number(min, max)`

*Alias*: `number`

Inserts an integer in the given range into the document.

#### Arguments

| Argument | Description |
| -------- | ----------- |
| `min`      | Minimum value of inserted integer. *Default: 10*. *Optional*  |
| `max`      | Maximum value of inserted integer |

#### Example
```python
from monufacture.helpers import number


document("user", {
    "age":  number(18, 35)
})

```

---

### `date([[[[[[[year], month], day], hour], minute], second], microsecond])`

Inserts a datetime object set to the given time/date. If no arguments are provided, the current datetime is inserted.

#### Arguments

| Argument | Description |
| -------- | ----------- |
| year          | The year. *Optional*        | 
| month         | The month. *Optional*       | 
| day           | The day. *Optional*         | 
| hour          | The hour. *Optional*        | 
| minute        | The minute. *Optional*      |     
| second        | The second. *Optional*      |     
| microsecond   | The microsecond. *Optional* |                 

#### Example
```python
from monufacture.helpers import date


document("blogpost", {
    "published":        date(2010, 2, 3, 4, 5, 6),  # A specific date
    "last_viewed":      date()                      # Right now
})

```

---

### `now()`

Inserts the current datetime. This is essentially the same as using the `date()` helper with no arguments.

#### Example
```python
from monufacture.helpers import date


document("blogpost", {
    "published":        now()
})

```

---

### `ago([[[[[[[years], months], days], hours], minutes], seconds], microseconds])`

Inserts a datetime set to a date and time a given period before the current date time. Remember, this helper is evaluated at build time, not declaration time. 

#### Arguments

| Argument | Description |
| -------- | ----------- |
| years        | The years to include in the delta. *Optional*        | 
| months       | The months to include in the delta. *Optional*       | 
| days         | The days to include in the delta. *Optional*         | 
| hours        | The hours to include in the delta. *Optional*        | 
| minutes      | The minutes to include in the delta. *Optional*      |     
| seconds      | The seconds to include in the delta. *Optional*      |     
| microseconds | The microseconds to include in the delta. *Optional* | 

#### Example
```python
from monufacture.helpers import ago


document("blogpost", {
    "published":        ago(hours=1, minutes=30)
})
```

---

### `from_now([[[[[[[years], months], days], hours], minutes], seconds], microseconds])`

Inserts a datetime set to a date and time a given period after the current date time. Remember, this helper is evaluated at build time, not declaration time. 

#### Arguments

| Argument | Description |
| -------- | ----------- |
| years        | The years to include in the delta. *Optional*        | 
| months       | The months to include in the delta. *Optional*       | 
| days         | The days to include in the delta. *Optional*         | 
| hours        | The hours to include in the delta. *Optional*        | 
| minutes      | The minutes to include in the delta. *Optional*      |     
| seconds      | The seconds to include in the delta. *Optional*      |     
| microseconds | The microseconds to include in the delta. *Optional* | 

#### Example
```python
from monufacture.helpers import from_now


document("credit_card", {
    "expires":        from_now(years=1, months=2)
})
```

---

### `list_of(fn, length)`

Used to insert a list of the given length containing the results of invoking a given other helper multiple times. Can be used together with the `embed` helper to insert multiple copies of a fragment as an embedded collection. 

#### Arguments

| Argument | Description |
| -------- | ----------- |
| fn       | A call to another helper function which will be used to yield the content of each list entry. |
| length   | The length of the required list. The given wrapped helper will be invoked this many times. |

#### Example
```python
from monufacture.helpers import list_of


fragment("player", {
    "name":         random_text(),
    "number":       sequence()
})

document("team", {
    "players":      list_of(embed("player"), 11)
    "coaches":      list_of(random_text(), 3)
})
```

---

### `object_id()`

Generates and inserts a new BSON ObjectId at build time. 

#### Example
```python
from monufacture.helpers import object_id


document("blogpost", {
    "_id":  object_id()
})

```

---

### `union(*fns)`

Allows the list output of other helper function calls (e.g. `list_of`) to be unioned into a single list at build time. 

#### Arguments

| Argument | Description |
| -------- | ----------- |
| `*fns`   | A list of calls to other helper functions, all of which must output lists. |

#### Example
```python
from monufacture.helpers import union


fragment("player", {
    "name":         random_text(),
    "number":       sequence()
})

fragment("injured_player", {
    "is_injured":   True
}, parent="player")

document("team", {
    "players":      union(list_of(embed("player"), 8), list_of(embed("injured"), 3))
})
```

---

### `one_of(*values)`

Allows a list of possible value to be provided for a field. At build time one of the supplied values will be picked at random and inserted. 

#### Arguments

| Argument | Description |
| -------- | ----------- |
| *values  | The list of possible values the intended field can take. |

#### Example
```python
from monufacture.helpers import one_of


document("user", {
    "status":       one_of('NEW', 'ACT', 'DEL')
})

```


## Writing Custom Helpers

As well as the out-of-the-box helpers documented in the previous section, you are of course free to implement your own custom helpers to meet the needs of you specific business domain. 

Implementing a custom helper couldn't be easier. A helper is just a function that accepts whatever specific arguments it needs and returns a function to be called at build time which should return the actual value to be inserted in the document. The returned function should accept the document as its only argument.

### Example
```python
# A custom helper which inserts a token
def token():
    def build(obj):
        return str(uuid.uuid4().hex)

    return build
```


## Using Factories

Once some factories have been declared, Monufacture let's you use factories to generate documents via two main routes: "building" and "creating".

### Building Documents

"Building" a document means generating an instance using the factory without saving it in the database. Building supports a variety of options:

```python
from monufacture import build, build_list


# Build the default document from the "car" factory
car = build("car")


# Build the "mazda" document from the "car" factory
mazda = build("car", "mazda")


# Build the default document from the "car" factory overriding the value for the "wheels" attribute
three_wheeler = build("car", wheels=3)


# Build a list of 5 cars
cars = build_list(5, "car")


# Build a list of 10 mazdas
mazdas = build_list(10, "car", "mazda")


# Build a list of 7 cars, overriding the "wheels" attribute on each
three_wheelers = build_list(7, "car", wheels=3)

```
Note:
 - Overrides will be inserted into the document whether the given attribute already exists or not. 


### Creating Documents

The API for "creating" document is essentially identical to that for "building", the only difference is that when creating a document, it is inserted into the MongoDB collection associated with the factory and is given an `_id`. 

```python
from monufacture import create, create_list


# Create the default document from the "car" factory
car = create("car")


# Create the "mazda" document from the "car" factory
mazda = create("car", "mazda")


# Create the default document from the "car" factory overriding the value for the "wheels" attribute
three_wheeler = create("car", wheels=3)


# Create a list of 5 cars
cars = create_list(5, "car")


# Create a list of 10 mazdas
mazdas = create_list(10, "car", "mazda")


# Create a list of 7 cars, overriding the "wheels" attribute on each
three_wheelers = build_list(7, "car", wheels=3)
```

### Cleanup

Typically, test documents are created in the context of a unit test and are no longer of use after that test has completed. 

To ensure the created test documents are cleared up, use the `cleanup` method from you test's tearDown method:

```python
from unittest import TestCase
from monufacture import create, cleanup


class BlogpostTestCase(TestCase):
    
    def test_something(self):
        post = create("blogpost")
        # do some testing

    def tearDown(self)
        cleanup()
```

### Debugging

Monufacture has some basic debug logging which can be turned on from your test to aid debugging. 

```python
import monufacture

monufacture.debug = True
```

Debug logging currently outputs a log entry each time a document is created.