# Object Caching
There are certain scenarios where you may want to cache an object such as a database connection, HTTP client or ML model. `cachex.cache_reference` is an easy way to cache unhashable objects and make them available globally throughout an application. It is a very easy way to implement the singleton design pattern. Both sync and async functions are supported.

Singletons are fairly common in web API's (anyone who has used SQLAlchemy will probably remember this `engine = create_engine("sqlite+pysqlite:///:memory:")`). The engine is an object that you declare at the module level and use throughout your application. Not all objects are designed to be initialized this way. In many cases, a global object needs to be initialized in a function. Global(like) objects are discussed in the FastAPI documentation. The recommended solution is to use [lifespan events](https://fastapi.tiangolo.com/advanced/events/) and store your objects the application's `state` attribute or a global collection. In many cases, this is the correct solution. If your API is serving an ML model, the model should be loaded on application start.


- **Lazy Initialization**: Creating objects when needed on demand ensures resources are not unecessarily allocated. If the initialization of an object is not prohibitively slow, and is only used for a subset of endpoints, it may make sense initialize that object when needed rather than on application start.
- **Dynamic Configuration**: The configuration of an object may vary based on user input (or the user themselves). It may not be feasible to initialize all objects at startup. The example below illustrates a per-user database configuration using SQLLite (in a real application you'd want to authenticate the user and make sure only authenticated users are accessing their data)...

```python
import sqlite3
from typing import Annotated

from cachex import cche_reference
from fastapi import Depends, FastAPI


app = FastAPI()


@cache_reference()
def get_conn(user: str) -> sqlite3.Connection:
    """Create a DB file for the user."""
    conn = sqlite3.connect(f"{user}.db")
    # Just for the sake of the example we will create a table and populate some data.
    # It will be the same data for all users
    cur = conn.cursor()
    cur.execute("CREATE TABLE movie(title, year, score)")
    cur.execute("""
        INSERT INTO movie VALUES
            ('Monty Python and the Holy Grail', 1975, 8.2),
            ('And Now for Something Completely Different', 1971, 7.5)
    """)
    return conn


@app.get("/name/{user}")
def get_movie_name(conn: Annotated[sqlite3.Connection, Depends(get_conn)]) -> str:
    """Query data from the user's database."""
    cur = conn.cursor()
    result = cur.execute("SELECT title FRON movie")
    return result.fetchone()[0]
```