import psycopg2
import yaml
import argparse
import time

def create_replication_user(connection, repl_username, repl_password):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (repl_username,))
        if cursor.fetchone() is None:
            cursor.execute(f"CREATE ROLE {repl_username} WITH REPLICATION LOGIN PASSWORD %s", (repl_password,))
            print(f"User '{repl_username}' created.")
        else:
            print(f"User '{repl_username}' already exists.")

def create_publication(connection, publication_name):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1 FROM pg_publication WHERE pubname=%s", (publication_name,))
        if cursor.fetchone() is None:
            command = f"CREATE PUBLICATION {publication_name} FOR ALL TABLES;"
            print(f"Creating publication '{publication_name}' with command: {command}")
            cursor.execute(command)
            print(f"Publication '{publication_name}' created for all tables.")
        else:
            print(f"Publication '{publication_name}' already exists.")

def create_subscription(connection, subscription_name, slot_name, repl_username, repl_password, source_config):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1 FROM pg_subscription WHERE subname=%s", (subscription_name,))
        if cursor.fetchone() is None:
            command = f"""
                CREATE SUBSCRIPTION {subscription_name}
                CONNECTION 'host={source_config['vpn_host']} port={source_config['port']} dbname={source_config['dbname']} user={repl_username} password={repl_password}'
                PUBLICATION {source_config['publication_name']} WITH (copy_data = false, origin = none, slot_name = '{slot_name}');
            """
            print(f"Creating subscription '{subscription_name}' with command: {command}")
            cursor.execute(command)
            print(f"Subscription '{subscription_name}' created.")
        else:
            print(f"Subscription '{subscription_name}' already exists.")

def remove_subscriptions(connection):
    with connection.cursor() as cursor:
        cursor.execute("SELECT subname FROM pg_subscription;")
        subscriptions = cursor.fetchall()
        for sub in subscriptions:
            sub_name = sub[0]
            # disable subscription before dropping
            cursor.execute(f"ALTER SUBSCRIPTION {sub_name} DISABLE;")
            # set slot to none before dropping
            cursor.execute(f"ALTER SUBSCRIPTION {sub_name} SET (slot_name = NONE);")
            cursor.execute(f"DROP SUBSCRIPTION {sub_name};")
            print(f"Subscription '{sub_name}' dropped.")

def remove_publications(connection):
    with connection.cursor() as cursor:
        cursor.execute("SELECT pubname FROM pg_publication;")
        publications = cursor.fetchall()
        for pub in publications:
            pub_name = pub[0]
            cursor.execute(f"DROP PUBLICATION {pub_name};")
            print(f"Publication '{pub_name}' dropped.")

def connect_to_db(config):
    return psycopg2.connect(
        host=config['host'],
        port=config['port'],
        dbname=config['dbname'],
        user=config['user'],
        password=config['password']
    )

def process_server(config, repl_username, repl_password, create_repl_user_only, all_configs, is_land_server=False):
    connection = None
    try:
        connection = connect_to_db(config)
        connection.autocommit = True
        create_replication_user(connection, repl_username, repl_password)
        if create_repl_user_only:
            if connection:
                connection.close()
            return
        
        # wait for 1 seconds for the replication user to be created
        print("Waiting for 1 seconds for the replication user to be created...")
        time.sleep(1)

        for other_config in all_configs:
            if other_config != config:
                subscription_name = f"ship_{other_config['name']}_subscription"
                slot_name = f"from_{config['name']}_to_{other_config['name']}_sub_slot"
                create_subscription(connection, subscription_name, slot_name, repl_username, repl_password, other_config)
    except Exception as e:
        print(f"Error connecting to {config['host']}:{config['port']} - {e}")
    finally:
        if connection:
            connection.close()

def create_resolve_conflicts_handling_triggers(connection):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.columns 
            WHERE column_name = 'write_date' AND table_schema = 'public';
        """)
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            trigger_function = f"""
            CREATE OR REPLACE FUNCTION {table_name}_resolve_conflict() RETURNS TRIGGER AS $$
            BEGIN
                -- Debug logging
                RAISE NOTICE 'Trigger called on table: {table_name}, OLD.write_date: %, NEW.write_date: %', OLD.write_date, NEW.write_date;
                
                -- Check if NEW.write_date or OLD.write_date is NULL
                IF NEW.write_date IS NULL OR OLD.write_date IS NULL THEN
                    RAISE WARNING 'NULL write_date detected on table: {table_name}, OLD.write_date: %, NEW.write_date: %', OLD.write_date, NEW.write_date;
                    RETURN NEW;
                END IF;

                IF NEW.write_date >= OLD.write_date THEN
                    RAISE NOTICE 'NEW row accepted on table: {table_name}, NEW.write_date: %', NEW.write_date;
                    RETURN NEW;
                ELSE
                    RAISE NOTICE 'OLD row retained on table: {table_name}, OLD.write_date: %', OLD.write_date;
                    RETURN OLD;
                END IF;
            END;
            $$ LANGUAGE plpgsql;
            """
            cursor.execute(trigger_function)
            
            # Drop the trigger if it already exists
            drop_trigger = f"""
            DROP TRIGGER IF EXISTS resolve_conflict_trigger ON {table_name};
            """
            cursor.execute(drop_trigger)
            
            # Create the trigger
            trigger_creation = f"""
            CREATE TRIGGER resolve_conflict_trigger
            BEFORE UPDATE ON {table_name}
            FOR EACH ROW
            EXECUTE FUNCTION {table_name}_resolve_conflict();
            """
            cursor.execute(trigger_creation)
            
            # Enable the trigger always
            enable_trigger = f"""
            ALTER TABLE {table_name}
            ENABLE ALWAYS TRIGGER resolve_conflict_trigger;
            """
            cursor.execute(enable_trigger)
            
            print(f"Conflict resolution trigger created and enabled always for table {table_name}")

def remove_resolve_conflicts_handling_triggers(connection):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.columns 
            WHERE column_name = 'write_date' AND table_schema = 'public';
        """)
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            trigger_removal = f"""
            DROP TRIGGER IF EXISTS resolve_conflict_trigger ON {table_name};
            DROP FUNCTION IF EXISTS {table_name}_resolve_conflict();
            """
            cursor.execute(trigger_removal)
            print(f"Conflict resolution trigger removed for table {table_name}")

def main():
    parser = argparse.ArgumentParser(description='Create replication user, publication, and subscriptions in PostgreSQL databases.')
    subparsers = parser.add_subparsers(dest='command')

    repl_setup = subparsers.add_parser('repl', help="Create replication")
    repl_setup.add_argument('--config_file', help='Path to the YAML configuration file.')
    repl_setup.add_argument('--repl_username', default='replicator', help='Username for the replication user.')
    repl_setup.add_argument('--repl_password', help='Password for the replication user.')
    repl_setup.add_argument('--publication_name', nargs='?', default='qlt_publication', help='Name of the publication to create (default: qlt_publication).')
    repl_setup.add_argument('--create_repl_user_only', action='store_true', help='Only create replication user and exit.')

    repl_removal = subparsers.add_parser('remove', help="Remove replication settings in all servers.")
    repl_removal.add_argument('--config_file', help='Path to the YAML configuration file.')

    trigger_add = subparsers.add_parser('add_triggers', help="Add triggers to handle duplicate key errors.")
    trigger_add.add_argument('--config_file', help='Path to the YAML configuration file.')

    trigger_remove = subparsers.add_parser('remove_triggers', help="Remove triggers and functions handling duplicate key errors.")
    trigger_remove.add_argument('--config_file', help='Path to the YAML configuration file.')

    args = parser.parse_args()

    if args.command == 'repl':
        config_file, repl_username, repl_password, create_repl_user_only = \
            args.config_file, args.repl_username, args.repl_password, args.create_repl_user_only
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)

        config['land_server']['name'] = 'land'

        all_configs = [config['land_server']] + config['ship_servers']

        # for each server, create publication
        for server_config in all_configs:
            connection = connect_to_db(server_config)
            connection.autocommit = True
            create_publication(connection, server_config['publication_name'])
            connection.close()

        # Process land server
        print(f"----------Processing land server at {config['land_server']['host']}...")
        process_server(config['land_server'], repl_username, repl_password, create_repl_user_only, all_configs, is_land_server=True)

        # Process ship servers
        for ship_config in config['ship_servers']:
            print(f"----------Processing ship server at {ship_config['host']}...")
            process_server(ship_config, repl_username, repl_password, create_repl_user_only, all_configs)
    elif args.command == 'remove':
        config_file = args.config_file
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)

        # Remove subscriptions and publications from all servers
        for server_config in [config['land_server']] + config['ship_servers']:
            connection = connect_to_db(server_config)
            connection.autocommit = True
            remove_subscriptions(connection)
            remove_publications(connection)
            connection.close()
    elif args.command == 'add_triggers':
        config_file = args.config_file
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)

        # create insert dup_key error handling triggers for all servers
        for server_config in [config['land_server']] + config['ship_servers']:
            print(f"*********Creating resolve conflict handling triggers for {server_config['host']}...")
            connection = connect_to_db(server_config)
            connection.autocommit = True
            create_resolve_conflicts_handling_triggers(connection)
            connection.close()
    elif args.command == 'remove_triggers':
        config_file = args.config_file
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)

        for server_config in [config['land_server']] + config['ship_servers']:
            print(f"*********Removing insert duplicate key error handling triggers for {server_config['host']}...")
            connection = connect_to_db(server_config)
            connection.autocommit = True
            remove_resolve_conflicts_handling_triggers(connection)
            connection.close()

if __name__ == "__main__":
    main()
