# Introduction

This manual provides a comprehensive guide to the design and architecture of the API, aiming to streamline the work of future contributors and maintainers. It covers the technical stack, design principles, and implementation details to ensure clarity and ease of understanding.

# Architecture

This project adheres to the core principles of [microservices architecture](https://learn.microsoft.com/en-us/azure/architecture/microservices/), emphasizing modularity, scalability, and independence of components. Specifically, it adopts a "triangle architecture," characterized by its three key components: the main API, the authentication API, and the client. This structure ensures clear separation of concerns, enabling each component to function autonomously while seamlessly integrating within the overall system.

# Tech Stack

The API ecosystem consists of three main components: the primary API, the authentication API, and the log API.  
All three are built using Flask, adhering to its common design principles.  
However, they differ in their implementation approaches based on their complexity and use cases:

### Main API

The primary API is developed using the `flask_restful` extension, which facilitates the creation of a resource-based API.  
Each resource is encapsulated within a dedicated class that inherits from the `Resource` class provided by `flask_restful`.  
These classes implement abstract methods corresponding to HTTP methods such as `GET`, `POST`, or others as required. This modular approach ensures scalability and maintainability.

### Authentication and Log APIs

In contrast, the authentication API and the log API utilize Flask's decorator-based approach for defining endpoints. This method is chosen due to their relatively simple structure and limited number of endpoints, which can be efficiently managed within a single file.  
This approach reduces overhead while maintaining clarity for smaller, less complex APIs.

### Design Philosophy

The choice of implementation strategy for each API component reflects a balance between complexity and maintainability.  
The resource-based approach of `flask_restful` is ideal for larger, more intricate APIs, while the decorator-based method is well-suited for lightweight, straightforward APIs.