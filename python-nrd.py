import sys
import whois
from datetime import datetime, timedelta
import argparse
import concurrent.futures
import os
import time
import threading

lock = threading.Lock()

def is_registered_within_days(domain, days):
    try:
        domain_info = whois.whois(domain)
        registration_date = domain_info.creation_date

        if isinstance(registration_date, list):
            registration_date = registration_date[0]

        if registration_date:
            threshold_date = datetime.now() - timedelta(days=days)
            days_since_registration = (datetime.now() - registration_date).days
            if registration_date >= threshold_date:
                return 'within_interval', days_since_registration, registration_date
            else:
                return 'outside_interval', days_since_registration, registration_date
        else:
            return 'error', None, None  # Nessuna data di registrazione trovata
    except Exception as excp:
        return 'exception', str(excp), None  # Eccezione gestita come errore

def progress_bar(current, total, exceptions):
    text = f"\r[ DOMAINS {current}/{total} | ERRORS {exceptions} ]\r"
    length = len(text) + 1
    text_clean = "\r" + " " * length + "\r"
    return text, text_clean, length

def process_domain(domain, days, verbose, output_file, wait_time, counts, total_domains):
    result, extra_info, registration_date = is_registered_within_days(domain, days)
    output_str = ""

    if result == 'within_interval':
        output_str = f"{domain} {extra_info} NEWLY REGISTERED DOMAIN"
    elif result == 'outside_interval' and verbose >= 1:
        output_str = f"{domain} OLD"
    elif result == 'exception' and verbose >= 2:  # Eccezione o errore
        output_str = f"{domain} EXCEPTION {extra_info}"
        with lock:
            counts['errors'] += 1
    elif result == 'error' and verbose >= 1:  # Nessuna data di registrazione trovata
        output_str = f"{domain} ERROR"
        with lock:
            counts['errors'] += 1

    # Livello 3: mostra la data di registrazione
    if verbose == 3 and registration_date:
        output_str = f"{domain} {registration_date} {('NEWLY REGISTERED DOMAIN' if result == 'within_interval' else 'OLD')}"

    # Progresso: viene aggiornato indipendentemente dalla verbosità
    with lock:
        counts['domains'] += 1
    progress_bar_text, progress_bar_text_clean, progress_bar_length = progress_bar(counts['domains'], total_domains, counts['errors'])

    # Aggiorna la progress bar, anche se non c'è output
    sys.stdout.write(progress_bar_text_clean)
    if output_str:  # Stampa l'output solo se necessario
        print(output_str)
        if output_file:
            with open(output_file, 'a') as f:
                f.write(output_str + '\n')

    sys.stdout.write(progress_bar_text)
    sys.stdout.flush()

    if wait_time > 0:
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
                    '\nOutput format: domain [status]. For newly registered domains, the number of days since registration is also shown.\n',
        usage='%(prog)s [options] -i input_file',
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument("-i", "--input", required=True, help="File containing the list of domains (one per line)")
    parser.add_argument("-o", "--output", help="File to write the output")
    parser.add_argument("-t", "--time", type=int, default=365, help="Number of days to check registration against (default: 365)")
    parser.add_argument("-v", "--verbose", type=int, choices=[0, 1, 2, 3], default=0, help="""
                        Set verbosity level (default: 0):
                        0 - Show only newly registered domains
                        1 - Show newly registered domains, old domains, errors
                        2 - Show newly registered domains, old domains, errors, exceptions
                        3 - Show newly registered domains, old domains, errors, exceptions, registration date (for debugging)
                        """)
    parser.add_argument("-x", "--threads", action="store_true", help="Enable multithreaded checking for faster execution")
    parser.add_argument("-y", "--yes", action="store_true", help="Automatically overwrite the output file if it exists")
    parser.add_argument("-w", "--wait", type=int, default=0, help="Time to wait (in seconds) between WHOIS requests (default: 0)")

    args = parser.parse_args()

    if args.output:
        check_output_file(args.output, args.yes)

    try:
        with open(args.input, 'r') as file:
            domains = [line.strip() for line in file]

            total_domains = len(domains)
            counts = {'domains': 0, 'errors': 0}

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
                        total_domains
                    ) for domain in domains]
                for future in concurrent.futures.as_completed(futures):
                    future.result()
        else:
            for domain in domains:
                process_domain(domain, args.time, args.verbose, args.output, args.wait, counts, total_domains)

    except FileNotFoundError:
        print(f"Error: file {args.input} not found!")
        sys.exit(1)

if __name__ == "__main__":
    main()
