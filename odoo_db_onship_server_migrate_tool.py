#!/usr/bin/env python3

import argparse
import psycopg2
from psycopg2 import sql
import json
import os

SEQUENCE_PADDING = 1000000000000

def get_sequences(conn, schema=None, prefix=None, exclude_prefix=None):
    query = """
        SELECT sequence_schema, sequence_name 
        FROM information_schema.sequences
        WHERE sequence_catalog = current_database()
    """
    conditions = []
    params = []

    if schema:
        conditions.append("sequence_schema = %s")
        params.append(schema)

    if prefix:
        conditions.append("sequence_name LIKE %s")
        params.append(prefix + '%')
    
    if exclude_prefix:
        conditions.append("sequence_name NOT LIKE %s")
        params.append(exclude_prefix + '%')

    if conditions:
        query += " AND " + " AND ".join(conditions)

    with conn.cursor() as cur:
        cur.execute(query, tuple(params))
        sequences = cur.fetchall()
    return sequences

def get_int_columns(conn, schema=None):
    query = """
        SELECT table_schema, table_name, column_name 
        FROM information_schema.columns 
        WHERE ( data_type = 'integer' OR data_type = 'int4' )
        AND table_schema NOT IN ('information_schema', 'pg_catalog')
    """
    if schema:
        query += " AND table_schema = %s"
        params = (schema,)
    else:
        params = ()
    
    with conn.cursor() as cur:
        cur.execute(query, params)
        columns = cur.fetchall()
    return columns

def convert_column_to_bigint(conn, table_schema, table_name, column_name):
    with conn.cursor() as cur:
        try:
            alter_table_query = sql.SQL("""
                ALTER TABLE {schema}.{table}
                ALTER COLUMN {column} TYPE bigint
                USING {column}::bigint
            """).format(
                schema=sql.Identifier(table_schema),
                table=sql.Identifier(table_name),
                column=sql.Identifier(column_name)
            )
            cur.execute(alter_table_query)
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error converting {table_schema}.{table_name}.{column_name} to bigint: {e}")
            raise e
        print(f"Converted {table_schema}.{table_name}.{column_name} to bigint.")

def get_sequence_last_value(conn, sequence_schema, sequence_name):
    with conn.cursor() as cur:
        try:
            last_value_query = f"SELECT last_value FROM {sequence_schema}.{sequence_name}"
            cur.execute(last_value_query)
            last_value = cur.fetchone()[0]
        except Exception as e:
            print(f"Error getting last_value of sequence {sequence_schema}.{sequence_name}: {e}")
            raise e
        print(f"Got last_value of sequence {sequence_schema}.{sequence_name}: {last_value}.")
        return last_value

def set_sequence_last_value(conn, sequence_schema, sequence_name, last_value):
    with conn.cursor() as cur:
        try:
            setval_query = sql.SQL("""
                SELECT setval({schema_sequence}, %s, true)
            """).format(
                schema_sequence=sql.Literal(sequence_schema+"."+sequence_name),
            )
            cur.execute(setval_query, [last_value])
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error setting last_value of sequence {sequence_schema}.{sequence_name}: {e}")
            raise e
        print(f"Set last_value of sequence {sequence_schema}.{sequence_name} to {last_value}.")

def convert_sequence_to_bigint(conn, sequence_schema, sequence_name):
    with conn.cursor() as cur:
        try:
            alter_seq_query = sql.SQL("""
                ALTER SEQUENCE {schema}.{sequence}
                AS bigint
            """).format(
                schema=sql.Identifier(sequence_schema),
                sequence=sql.Identifier(sequence_name)
            )
            cur.execute(alter_seq_query)
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error converting sequence {sequence_schema}.{sequence_name} to bigint: {e}")
            raise e
        print(f"Converted sequence {sequence_schema}.{sequence_name} to bigint.")

def backup_sequences_last_value(conn, schema, ship_no, host):
    sequences = get_sequences(conn, schema)
    backup = {}
    for sequence_schema, sequence_name in sequences:
        try:
            last_value = get_sequence_last_value(conn, sequence_schema, sequence_name)
            backup[f"{sequence_schema}.{sequence_name}"] = last_value
        except Exception as e:
            print(f"Error backing up last_value of sequence {sequence_schema}.{sequence_name}: {e}")
    backup_filename = f"host-{host}_ship-{ship_no}.json"
    with open(backup_filename, 'w') as backup_file:
        json.dump(backup, backup_file)
    print(f"Backed up sequence last_values to {backup_filename}")

def restore_sequences_last_value(conn, backup_file):
    if not os.path.exists(backup_file):
        print(f"Backup file {backup_file} does not exist.")
        return

    with open(backup_file, 'r') as bf:
        backup = json.load(bf)

    failed_sequences = []
    for sequence, last_value in backup.items():
        sequence_schema, sequence_name = sequence.split('.')
        try:
            set_sequence_last_value(conn, sequence_schema, sequence_name, last_value)
        except Exception as e:
            failed_sequences.append((sequence_schema, sequence_name))
            print(f"Error restoring last_value of sequence {sequence_schema}.{sequence_name}: {e}")

    if failed_sequences:
        print("Failed to restore last_value for the following sequences:")
        for sequence_schema, sequence_name in failed_sequences:
            print(f"{sequence_schema}.{sequence_name}")
    else:
        print(f"Successfully restored sequences' last values from {backup_file}")

def main():
    parser = argparse.ArgumentParser(description="Database Maintenance Tool")
    subparsers = parser.add_subparsers(dest='command')

    # Subcommand for converting int columns to bigint
    convert_int_parser = subparsers.add_parser('convert_int_to_bigint', help="Convert int columns to bigint")
    convert_int_parser.add_argument("--host", required=True, help="Database host")
    convert_int_parser.add_argument("--port", type=int, default=5432, help="Database port")
    convert_int_parser.add_argument("--dbname", required=True, help="Database name")
    convert_int_parser.add_argument("--user", required=True, help="Database user")
    convert_int_parser.add_argument("--password", required=True, help="Database password")
    convert_int_parser.add_argument("--schema", default="public", help="Schema to filter tables (optional)")

    # Subcommand for setting sequence last_value
    set_seq_value_parser = subparsers.add_parser('set_sequence_last_value', help="Set last_value of sequences")
    set_seq_value_parser.add_argument("--host", required=True, help="Database host")
    set_seq_value_parser.add_argument("--port", type=int, default=5432, help="Database port")
    set_seq_value_parser.add_argument("--dbname", required=True, help="Database name")
    set_seq_value_parser.add_argument("--user", required=True, help="Database user")
    set_seq_value_parser.add_argument("--password", required=True, help="Database password")
    set_seq_value_parser.add_argument("--last_value", type=int, required=True, help="Value to set for the last_value of sequences")
    set_seq_value_parser.add_argument("--schema", default="public", help="Schema to filter sequences (optional)")
    set_seq_value_parser.add_argument("--prefix", help="Prefix to filter sequence names (optional)")
    set_seq_value_parser.add_argument("--ship_no", type=int, required=True, help="Ship number. Start from 1. E.g: ship 1 should be 1, ship 2 should be 2")

    # Subcommand for converting sequences to bigint
    convert_seq_to_bigint_parser = subparsers.add_parser('convert_sequences_to_bigint', help="Convert sequences to bigint")
    convert_seq_to_bigint_parser.add_argument("--host", required=True, help="Database host")
    convert_seq_to_bigint_parser.add_argument("--port", type=int, default=5432, help="Database port")
    convert_seq_to_bigint_parser.add_argument("--dbname", required=True, help="Database name")
    convert_seq_to_bigint_parser.add_argument("--user", required=True, help="Database user")
    convert_seq_to_bigint_parser.add_argument("--password", required=True, help="Database password")
    convert_seq_to_bigint_parser.add_argument("--schema", default="public", help="Schema to filter sequences (optional)")
    convert_seq_to_bigint_parser.add_argument("--prefix", help="Prefix to filter sequence names (optional)")

    migrate_onship_parser = subparsers.add_parser('migrate_onship_server', help="Migrate an odoo db operated on-ship server")
    migrate_onship_parser.add_argument("--host", required=True, help="Database host")
    migrate_onship_parser.add_argument("--port", type=int, default=5432, help="Database port")
    migrate_onship_parser.add_argument("--dbname", required=True, help="Database name")
    migrate_onship_parser.add_argument("--user", required=True, help="Database user")
    migrate_onship_parser.add_argument("--password", required=True, help="Database password")
    migrate_onship_parser.add_argument("--schema", default="public", help="Schema to filter tables (optional)")
    migrate_onship_parser.add_argument("--ship_no", type=int, required=True, help="Ship number. Start from 1. E.g: ship 1 should be 1, ship 2 should be 2")

    restore_seq_parser = subparsers.add_parser('restore_sequences', help="Restore sequences' last values from a JSON file")
    restore_seq_parser.add_argument("--host", required=True, help="Database host")
    restore_seq_parser.add_argument("--port", type=int, default=5432, help="Database port")
    restore_seq_parser.add_argument("--dbname", required=True, help="Database name")
    restore_seq_parser.add_argument("--user", required=True, help="Database user")
    restore_seq_parser.add_argument("--password", required=True, help="Database password")
    restore_seq_parser.add_argument("--backup_file", required=True, help="Path to the JSON file with backup data")

    args = parser.parse_args()

    conn = None
    try:
        conn = psycopg2.connect(
            host=args.host,
            port=args.port,
            dbname=args.dbname,
            user=args.user,
            password=args.password
        )

        if args.command == 'convert_int_to_bigint':
            failed_columns = []
            columns = get_int_columns(conn, args.schema)
            for table_schema, table_name, column_name in columns:
                try:
                    convert_column_to_bigint(conn, table_schema, table_name, column_name)
                except Exception as e:
                    failed_columns.append((table_schema, table_name, column_name))
            if failed_columns:
                print("Failed to convert the following columns:")
                for table_schema, table_name, column_name in failed_columns:
                    print(f"{table_schema}.{table_name}.{column_name}")

        elif args.command == 'set_sequence_last_value':
            backup_sequences_last_value(conn, args.schema, args.ship_no, args.host)
            failed_sequences = []
            sequences = get_sequences(conn, args.schema, args.prefix)
            for sequence_schema, sequence_name in sequences:
                try:
                    set_sequence_last_value(conn, sequence_schema, sequence_name, args.last_value)
                except Exception as e:
                    failed_sequences.append((sequence_schema, sequence_name))
            if failed_sequences:
                print("Failed to set last_value for the following sequences:")
                for sequence_schema, sequence_name in failed_sequences:
                    print(f"{sequence_schema}.{sequence_name}")

        elif args.command == 'convert_sequences_to_bigint':
            failed_sequences = []
            sequences = get_sequences(conn, args.schema, args.prefix)
            for sequence_schema, sequence_name in sequences:
                try:
                    convert_sequence_to_bigint(conn, sequence_schema, sequence_name)
                except Exception as e:
                    failed_sequences.append((sequence_schema, sequence_name))
            if failed_sequences:
                print("Failed to convert the following sequences:")
                for sequence_schema, sequence_name in failed_sequences:
                    print(f"{sequence_schema}.{sequence_name}")

        elif args.command == 'migrate_onship_server':
            print(f"Migrating on-ship server for ship number {args.ship_no}")
            backup_sequences_last_value(conn, args.schema, args.ship_no, args.host)

            # convert_int_columns
            failed_columns = []
            columns = get_int_columns(conn, args.schema)
            for table_schema, table_name, column_name in columns:
                try:
                    convert_column_to_bigint(conn, table_schema, table_name, column_name)
                except Exception as e:
                    failed_columns.append((table_schema, table_name, column_name))
            if failed_columns:
                print("Failed to convert the following columns:")
                for table_schema, table_name, column_name in failed_columns:
                    print(f"{table_schema}.{table_name}.{column_name}")

            # convert_sequences
            failed_sequences = []
            sequences = get_sequences(conn, args.schema)
            for sequence_schema, sequence_name in sequences:
                try:
                    convert_sequence_to_bigint(conn, sequence_schema, sequence_name)
                except Exception as e:
                    failed_sequences.append((sequence_schema, sequence_name))
            if failed_sequences:
                print("Failed to convert the following sequences:")
                for sequence_schema, sequence_name in failed_sequences:
                    print(f"{sequence_schema}.{sequence_name}")
            if int(args.ship_no) == 0:
                return
            # set_sequence_last_value
            failed_sequences = []
            sq_start_from = int(args.ship_no) * SEQUENCE_PADDING
            sq_end_at = (int(args.ship_no) + 1) * SEQUENCE_PADDING - 1
            sequences = get_sequences(conn, args.schema)
            for sequence_schema, sequence_name in sequences:
                try:
                    # if last_value is less than the start value, set it to the start value
                    # this is to prevent overwriting the sequence value which is already migrated
                    last_value = get_sequence_last_value(conn, sequence_schema, sequence_name)
                    if last_value < sq_start_from or last_value > sq_end_at:
                        set_sequence_last_value(conn, sequence_schema, sequence_name, sq_start_from)
                    else:
                        print(f"Skipping setting last_value for {sequence_schema}.{sequence_name} as it is already migrated.")
                except Exception as e:
                    failed_sequences.append((sequence_schema, sequence_name))
            if failed_sequences:
                print("Failed to set last_value for the following sequences:")
                for sequence_schema, sequence_name in failed_sequences:
                    print(f"{sequence_schema}.{sequence_name}")

        elif args.command == 'restore_sequences':
            restore_sequences_last_value(conn, args.backup_file)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
