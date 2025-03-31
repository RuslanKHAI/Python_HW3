CREATE_TABLES_SQL = [
    """
    DROP TABLE IF EXISTS links;
    """,
    """
    DROP TABLE IF EXISTS users;
    """,
    """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        auth_token TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS links (
        id SERIAL PRIMARY KEY,
        client_id INTEGER,
        long_link VARCHAR(255) NOT NULL,
        short_link VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP,
        sign_up_create_account BOOLEAN DEFAULT FALSE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS statistics (
        id SERIAL PRIMARY KEY,
        short_link VARCHAR(255) NOT NULL,
        access_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS expired_links (
        id SERIAL PRIMARY KEY,
        client_id INTEGER,
        long_link VARCHAR(255) NOT NULL,
        short_link VARCHAR(255) NOT NULL,
        created_at TIMESTAMP,
        expires_at TIMESTAMP,
        deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        sign_up_create_account BOOLEAN DEFAULT FALSE
    );
    """,
    """
    INSERT INTO users (id, auth_token)
    VALUES (1, 'token1'), (2, 'token2');
    """
]
