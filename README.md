# Cassandra GUI Client

A graphical desktop client for Apache Cassandra with full schema-driven CRUD support.

## Requirements

- Python 3.9+
- Apache Cassandra 3.x or 4.x

## Installation

1. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
Install dependencies:

pip install -r requirements.txt
Run the application:

python main.py

Configuration
Configuration is stored in ~/.cassandra_gui/config.json and is created automatically on first run.

Features
Multiple connection profiles
Keyspace and table discovery
Schema-driven dynamic forms
Paginated data browsing
Partition key filtering
Insert, update, and delete operations