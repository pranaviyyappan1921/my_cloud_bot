from sqlalchemy import text
from utils.database import get_engine


def create_tables():
    engine = get_engine()

    with engine.begin() as connection:

        connection.execute(text("""
            IF NOT EXISTS (
                SELECT * FROM sysobjects
                WHERE name='conversations' AND xtype='U'
            )
            CREATE TABLE conversations (
                id INT IDENTITY(1,1) PRIMARY KEY,
                session_id VARCHAR(255) NOT NULL,
                title VARCHAR(255) NOT NULL,
                created_at DATETIME2 DEFAULT GETUTCDATE(),
                updated_at DATETIME2 DEFAULT GETUTCDATE()
            )
        """))

        connection.execute(text("""
            IF NOT EXISTS (
                SELECT * FROM sysobjects
                WHERE name='messages' AND xtype='U'
            )
            CREATE TABLE messages (
                id INT IDENTITY(1,1) PRIMARY KEY,
                conversation_id INT NOT NULL,
                role VARCHAR(20) NOT NULL,
                content NVARCHAR(MAX) NOT NULL,
                created_at DATETIME2 DEFAULT GETUTCDATE(),

                CONSTRAINT FK_messages_conversations
                FOREIGN KEY (conversation_id)
                REFERENCES conversations(id)
                ON DELETE CASCADE
            )
        """))

        connection.execute(text("""
            IF NOT EXISTS (
                SELECT * FROM sysobjects
                WHERE name='uploaded_files' AND xtype='U'
            )
            CREATE TABLE uploaded_files (
                id INT IDENTITY(1,1) PRIMARY KEY,
                session_id VARCHAR(255) NOT NULL,
                file_name VARCHAR(255) NOT NULL,
                blob_name VARCHAR(500),
                file_type VARCHAR(100),
                uploaded_at DATETIME2 DEFAULT GETUTCDATE()
            )
        """))

    print("Azure SQL tables created successfully!")


if __name__ == "__main__":
    create_tables()