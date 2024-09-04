# python-nrd (wip)
Check domain registration dates and verify if they were registered within a specified number of days

## Usage
```
usage: python-nrd.py [options] -i input_file

Check domain registration dates and verify if they were registered within a specified number of days.
By default, only domains registered within the specified time frame are printed. Use -v to print all domains.

options:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        File containing the list of domains (one per line)
  -o OUTPUT, --output OUTPUT
                        File to write the output
  -t TIME, --time TIME  Number of days to check registration against (default: 365)
  -v, --verbose         Print all domains with the number of days since registration
  -x, --threads         Enable multithreaded checking for faster execution
  -y, --yes             Automatically overwrite the output file if it exists
  -w WAIT, --wait WAIT  Time to wait (in seconds) between WHOIS requests (default: 0)
```

## How to install dependencies (Arch Linux example)
```
sudo pacman -S python-pip
python -m venv ./.venv/whois
./.venv/whois/bin/pip install python-whois
```

## Sample output
```
 ./.venv/whois/bin/python python-nrd.py -x -t 365 -i list.txt
laluzinda.barcelona
peusdegat.barcelona

./.venv/whois/bin/python python-nrd.py -x -t 365 -v -i list.txt
google.it 9035
laluzinda.barcelona 3
peusdegat.barcelona 2
facebook.com 10021
abi.farm 373
```
