# python-nrd (wip)
Check domain registration dates and verify if they were registered within a specified number of days

## Usage
```
usage: python-nrd.py [options] -i input_file

Check domain registration dates and verify if they were registered within a specified number of days.
By default, only domains registered within the specified time frame are printed. Use -v to adjust output verbosity.

Output format: domain [status]. For newly registered domains, the number of days since registration is also shown.

options:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        File containing the list of domains (one per line)
  -o OUTPUT, --output OUTPUT
                        File to write the output
  -t TIME, --time TIME  Number of days to check registration against (default: 365)
  -v VERBOSE, --verbose VERBOSE
                        Set verbosity level (default: 0):
                        0 - Show only newly registered domains
                        1 - Show newly registered domains, old domains, errors
                        2 - Show newly registered domains, old domains, errors, exceptions
                        3 - Show newly registered domains, old domains, errors, exceptions, registration date (for debugging)
  -x, --threads         Enable multithreaded checking for faster execution
  -y, --yes             Automatically overwrite the output file if it exists
  -w WAIT, --wait WAIT  Time to wait (in seconds) between WHOIS requests (default: 0
```

## How to install dependencies (Arch Linux example)
```
sudo pacman -S python-pip
python -m venv ./.venv/whois
./.venv/whois/bin/pip install python-whois
```

## Sample output
```
 ./.venv/whois/bin/python python-nrd.py -w 1 -t 365 -i list.txt -v 1
laluzinda.barcelona 3 NEWLY REGISTERED DOMAIN
peusdegat.barcelona 2 NEWLY REGISTERED DOMAIN
blablabla ERROR
foobar ERROR
url273.e.read.ai ERROR
isher-paykel-ci804ctb1-ie-uk.html ERROR
ansen-fri-jh5.html ERROR
ritz-hansen-oxford-premium-3292a.html ERROR
nsa.html ERROR
www.xlmoto.it524299398myawv0dpx2 ERROR
www.xlmoto.it524299360myawv0dpx2 ERROR
career55.sapsf.eu ERROR
www.avverafinanziamenti ERROR
2.0.0.1 ERROR
click.a2aenergia.eu ERROR
01.emailinboundprocessing.eu ERROR
io.ox ERROR
www.chioggianotizie.it 181 NEWLY REGISTERED DOMAIN
agenparl.eu ERROR
[ DOMAINS 216/3931 | ERRORS 16 ]
```

## Tests
Test to verify the limits imposed by the default whois servers:
1. With command `python-nrd.py -w 1 -t 365 -i list.txt` errors started after 250~ queries
2. With command `python-nrd.py -x -t 365 -i list.txt` errors started after 80~ queries
