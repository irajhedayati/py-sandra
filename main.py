from cassandra.cluster import Cluster
import sys

def get_contact_points():
    print("Cassandra Connection Configuration")
    print("==================================")
    
    default_cp = "127.0.0.1"
    user_input = input(f"Enter contact points (comma-separated) [default: {default_cp}]: ").strip()
    
    if not user_input:
        return [default_cp]
    
    # Split by comma and strip whitespace from each entry
    return [cp.strip() for cp in user_input.split(',') if cp.strip()]

def main():
    contact_points = get_contact_points()
    
    print(f"\nAttempting to connect to: {contact_points}...")
    cluster = Cluster(contact_points)
    
    try:
        session = cluster.connect()
        print("Successfully connected to Cassandra cluster!")
        
        # Example: Execute a simple query
        row = session.execute("SELECT release_version FROM system.local").one()
        if row:
            print(f"Cassandra release version: {row.release_version}")
            
    except Exception as e:
        print(f"Error connecting to Cassandra: {e}", file=sys.stderr)
    finally:
        cluster.shutdown()

if __name__ == "__main__":
    main()
