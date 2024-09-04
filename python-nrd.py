#!/usr/bin/python

import sys
import whois
from datetime import datetime, timedelta
import argparse
import concurrent.futures
import os
import time

def is_registered_within_days(domain, days):
    try:
        domain_info = whois.whois(domain)
        registration_date = domain_info.creation_date

        if isinstance(registration_date, list):
            registration_date = registration_date[0]

        if registration_date:
            threshold_date = datetime.now() - timedelta(days=days)
            days_since_registration = (datetime.now() - registration_date).days
            return registration_date >= threshold_date, days_since_registration
        else:
            return False, None
    except Exception as e:
        return False, str(e)

def process_domain(domain, days, verbose, output_file=None, wait_time=0):
    is_registered, extra_info = is_registered_within_days(domain, days)
    output_str = ""

    if verbose:
        if isinstance(extra_info, int):
            output_str = f"{domain} {extra_info}"
        else:
            output_str = f"{domain} error"
    elif is_registered:
        output_str = domain

    if output_str:
        print(output_str)
        if output_file:
            with open(output_file, 'a') as f:
                f.write(output_str + '\n')

    if wait_time > 0:
        time.sleep(wait_time)

    return is_registered

def check_output_file(output_file, confirm):
    if os.path.exists(output_file) and not confirm:
        overwrite = input(f"The file '{output_file}' already exists. Do you want to overwrite it? (y/n): ").lower()
        if overwrite != 'y':
            print("Operation aborted by the user.")
            sys.exit(0)
        else:
            with open(output_file, 'w') as f:
                f.write("")  # Clear the file if user agrees to overwrite

def main():
    parser = argparse.ArgumentParser(
        description='Check domain registration dates and verify if they were registered within a specified number of days.\n'
                    'By default, only domains registered within the specified time frame are printed. Use -v to print all domains.\n',
        usage='%(prog)s [options] -i input_file',
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument("-i", "--input", required=True, help="File containing the list of domains (one per line)")
    parser.add_argument("-o", "--output", help="File to write the output")
    parser.add_argument("-t", "--time", type=int, default=365, help="Number of days to check registration against (default: 365)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print all domains with the number of days since registration")
    parser.add_argument("-x", "--threads", action="store_true", help="Enable multithreaded checking for faster execution")
    parser.add_argument("-y", "--yes", action="store_true", help="Automatically overwrite the output file if it exists")
    parser.add_argument("-w", "--wait", type=int, default=0, help="Time to wait (in seconds) between WHOIS requests (default: 0)")

    args = parser.parse_args()

    # Check if output file exists and if the user wants to overwrite
    if args.output:
        check_output_file(args.output, args.yes)

    try:
        with open(args.input, 'r') as file:
            domains = [line.strip() for line in file]

        if args.threads:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [
                    executor.submit(
                        process_domain,
                        domain,
                        args.time,
                        args.verbose,
                        args.output,
                        args.wait
                    ) for domain in domains]
                for future in concurrent.futures.as_completed(futures):
                    future.result()
        else:
            for domain in domains:
                process_domain(domain, args.time, args.verbose, args.output, args.wait)

    except FileNotFoundError:
        print(f"Error: file {args.input} not found!")
        sys.exit(1)

if __name__ == "__main__":
    main()
