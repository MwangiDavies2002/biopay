# MySQL

The Spring Boot service uses Flyway migrations in `services/payment-core/src/main/resources/db/migration`.

For local Docker Compose, MySQL is exposed on host port **3307** to reduce collision with an existing local MySQL install.

The application itself connects to MySQL over the Compose network at `mysql:3306`.
