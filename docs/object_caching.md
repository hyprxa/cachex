# Object Caching
There are certain scenarios where you may want to cache an object such as a database connection, HTTP client or ML model. `cachex.cache_reference` is an easy way to cache unhashable objects and make them available globally throughout an application. It is a very easy way to implement the singleton design pattern. Both sync and async functions are supported.

Object access across handlers is actually discussed in the FastAPI documentation. The recommended solution is to use [lifespan events](https://fastapi.tiangolo.com/advanced/events/) and store your objects to the application's `state` attribute or a global collection. In many cases, this is the correct solution, but (IMO) not all. For example, lifespan events do not support...

- **Lazy Initialization**: Creating objects when needed on demand ensures resources are not unecessarily allocated. If the initialization of an object is not prohibitively slow, and is only used for a subset of endpoints, it may make sense initialize that object when needed rather than on application start.
- **Dynamic Configuration**: 