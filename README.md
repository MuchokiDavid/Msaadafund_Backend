# Msaada Mshinani - Backend

Welcome to the backend repository for Msaada Mshinani, an automated donation platform dedicated to providing support and assistance to communities in need, with a focus on grassroots-level initiatives in Kenya.

## Overview

Msaada Mshinani's backend is built with Flask, a lightweight and versatile web framework for Python. This repository contains the backend codebase responsible for handling API requests, processing transactions, managing user accounts, and interacting with the database.

## Features

- **API Endpoints**: Define RESTful API endpoints to handle various functionalities, including user authentication, donation processing, charity management, and reporting.
- **Intersend Integration**: Utilize the Intersend API to handle transactions securely, ensuring reliable payment processing and donor verification.
- **Database Models**: Define database models using SQLAlchemy to represent entities such as users, charities, donations, and transaction history.
- **Data Seeding**: Populate the database with initial data using `seed.py`, including sample charities, users, and donation records for testing and development purposes.
- **Utilities**: Implement utility functions in the `utilities` directory to handle common tasks such as email notifications, data validation, and error handling.
- **Migration**: Perform database migrations using Flask-Migrate to manage changes to the database schema and ensure data integrity during development and deployment.

## Getting Started

To get started with the Msaada Mshinani backend, follow these steps:

1. Clone this repository to your local machine:

   ```bash
   git clone https://github.com/MuchokiDavid/MsaadaMashinani_Backend.git
    ```
2. Install dependencies using pip:

    ```bash
    pip install -r requirements.txt
    ```
3. Set up environment variables:
    - Create a `.env` file in the root directory
    - Define environment variables such as database connection URL, Intersend API credentials, and any other sensitive information.
    - Example:

        ```bash
        DATABASE_URL=postgresql://username:password@localhost:5432/msaada_mshinani
        INTERSEND_API_KEY=your-api-key
        INTERSEND_PUBLIC_KEY= your-key
        SECRET_KEY=your-secret-key
        ```
4. Perform database migration:

    ```bash
    cd server/
    flask db upgrade
    ```
5. Start the Flask development server:

    ```bash
    cd server/
    flask run
    ```
6. Test the API endpoints using tools like Postman or cURL.

## Technologies Used

* Flask: Lightweight web framework for building APIs in Python.
* SQLAlchemy: Object-relational mapping (ORM) library for database interactions.
* Flask-Migrate: Extension for database migrations with Flask.
* Intersend API: Third-party API for handling transactions securely.
* Python-dotenv: Library for loading environment variables from a .env file.

## Contributing

We welcome contributions from the community to help improve Msaada Mshinani. If you'd like to contribute, please follow these guidelines:

1. Fork the repository and create a new branch for your feature or bug fix.
2. Make your changes and ensure that tests and linting pass.
3. Submit a pull request with a clear description of your changes and the problem they solve.

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).

## Acknowledgements

1. [David Muchoki](https://github.com/MuchokiDavid)
2. [Clement Macharia](https://github.com/clementmw)
3. [Joseph Mang'ara](https://github.com/)
