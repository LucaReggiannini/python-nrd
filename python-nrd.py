import sys
import whois
from datetime import datetime, timedelta
import argparse
import concurrent.futures
import os
import time
import threading

lock = threading.Lock()

def load_cache(cache_file):
    cache = {}
    if cache_file and os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            for line in f:
                domain, date_str = line.strip().split()
                cache[domain] = datetime.strptime(date_str, '%Y-%m-%d')
    return cache

def update_cache(cache_file, domain, registration_date):
    if cache_file:
        with lock:
            with open(cache_file, 'a') as f:
                f.write(f"{domain} {registration_date.strftime('%Y-%m-%d')}\n")

def is_registered_within_days(domain, days, cache, cache_file):
    cache_hit = False
    if cache and domain in cache:
        registration_date = cache[domain]
        cache_hit = True
    else:
        try:
            domain_info = whois.whois(domain)
            registration_date = domain_info.creation_date
            if isinstance(registration_date, list):
                registration_date = registration_date[0]
            if registration_date:
                update_cache(cache_file, domain, registration_date)
            else:
                return 'error', None, None, False
        except Exception as excp:
            return 'exception', str(excp), None, False

    threshold_date = datetime.now() - timedelta(days=days)
    days_since_registration = (datetime.now() - registration_date).days
    if registration_date >= threshold_date:
        return 'within_interval', days_since_registration, registration_date, cache_hit
    else:
        return 'outside_interval', days_since_registration, registration_date, cache_hit

def progress_bar(current, total, newly_registered, exceptions, cache_hits, start_time):
    elapsed_time = datetime.now() - start_time
    hours, remainder = divmod(elapsed_time.total_seconds(), 3600)
    minutes, _ = divmod(remainder, 60)
    formatted_time = start_time.strftime("%H:%M %d/%m/%Y")
    text = f"\r[ DOMAINS {current}/{total} | NRD {newly_registered} | CACHE {cache_hits} | ERRORS {exceptions} | Start time: {formatted_time} (elapsed {int(hours):02d}:{int(minutes):02d}) ]\r"
    length = len(text) + 1
    text_clean = "\r" + " " * length + "\r"
    return text, text_clean, length

def process_domain(domain, days, verbose, output_file, wait_time, counts, total_domains, cache, cache_file, start_time):
    result, extra_info, registration_date, cache_hit = is_registered_within_days(domain, days, cache, cache_file)
    output_str = ""

    if result == 'within_interval':
        output_str = f"{domain} ({extra_info} days) NEWLY REGISTERED DOMAIN"
        with lock:
            counts['newly_registered'] += 1
    elif result == 'outside_interval' and verbose >= 2:
        output_str = f"{domain} ({extra_info} days) OLD"
    elif result == 'exception':
        with lock:
            counts['errors'] += 1
        if verbose >= 1:
            output_str = f"{domain} EXCEPTION {extra_info}"
    elif result == 'error':
        with lock:
            counts['errors'] += 1
        if verbose >= 1:
            output_str = f"{domain} ERROR"

    if verbose == 3 and registration_date:
        output_str = f"{domain} ({registration_date}) {('NEWLY REGISTERED DOMAIN' if result == 'within_interval' else 'OLD')}"
        if cache_hit:
            output_str += " (CACHE)"

    with lock:
        counts['domains'] += 1
        if cache_hit:
            counts['cache_hits'] += 1

    progress_bar_text, progress_bar_text_clean, progress_bar_length = progress_bar(
        counts['domains'], total_domains, counts['newly_registered'], counts['errors'], counts['cache_hits'], start_time
    )

    sys.stdout.write(progress_bar_text_clean)
    if output_str:
        print(output_str)
        if output_file:
            with open(output_file, 'a') as f:
                f.write(output_str + '\n')

    sys.stdout.write(progress_bar_text)
    sys.stdout.flush()

    if not cache_hit and wait_time > 0:
        time.sleep(wait_time)

    return result

def check_output_file(output_file, confirm):
    if os.path.exists(output_file) and not confirm:
        overwrite = input(f"The file '{output_file}' already exists. Do you want to overwrite it? (y/n): ").lower()
        if overwrite != 'y':
            print("Operation aborted by the user.")
            sys.exit(0)
        else:
            with open(output_file, 'w') as f:
                f.write("")

def main():
    parser = argparse.ArgumentParser(
        description='Check domain registration dates and verify if they were registered within a specified number of days.\n'
                    'By default, only domains registered within the specified time frame are printed. Use -v to adjust output verbosity.\n'
                    '\nOutput format: domain [status]. For newly registered domains, the number of days since registration is also shown.\n'
                    'For old domains, the number of days since registration is shown with the status "OLD".\n'
                    '\nIf a cache file is provided, domains found in cache will be checked without WHOIS request and no sleep time will be applied. ',
        usage='%(prog)s [options] -i input_file',
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument("-i", "--input", required=True, help="File containing the list of domains (one per line)")
    parser.add_argument("-o", "--output", help="File to write the output")
    parser.add_argument("-t", "--time", type=int, default=365, help="Number of days to check registration against (default: 365)")
    parser.add_argument("-v", "--verbose", type=int, choices=[0, 1, 2, 3], default=0, help="""
Set verbosity level (default: 0):
0 - Show only newly registered domains
1 - Show newly registered domains, errors, exceptions
2 - Show newly registered domains, errors, exceptions, old domains
3 - Show newly registered domains, errors, exceptions, old domains, registration date (for debugging)
The verbosity level set by -v does not affect internal logging from the "whois" library, which may still display errors or warnings.
                        """)
    parser.add_argument("-x", "--threads", action="store_true", help="Enable multithreaded checking for faster execution")
    parser.add_argument("-y", "--yes", action="store_true", help="Automatically overwrite the output file if it exists")
    parser.add_argument("-w", "--wait", type=int, default=0, help="Time to wait (in seconds) between WHOIS requests (default: 0)")
    parser.add_argument("-c", "--cache", help="File to use as cache for WHOIS requests. If a domain is found in cache, it will be checked without waiting.")

    args = parser.parse_args()

    if args.output:
        check_output_file(args.output, args.yes)

    cache = load_cache(args.cache) if args.cache else {}
    start_time = datetime.now()

    try:
        with open(args.input, 'r') as file:
            domains = [line.strip() for line in file]

            total_domains = len(domains)
            counts = {'domains': 0, 'newly_registered': 0, 'errors': 0, 'cache_hits': 0}

        if args.threads:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [
                    executor.submit(
                        process_domain,
                        domain,
                        args.time,
                        args.verbose,
                        args.output,
                        args.wait,
                        counts,
                        total_domains,
                        cache,
                        args.cache,
                        start_time
                    ) for domain in domains]
                for future in concurrent.futures.as_completed(futures):
                    future.result()
        else:
            for domain in domains:
                process_domain(domain, args.time, args.verbose, args.output, args.wait, counts, total_domains, cache, args.cache, start_time)

    except FileNotFoundError:
        print(f"Error: file {args.input} not found!")
        sys.exit(1)

if __name__ == "__main__":
    main()
