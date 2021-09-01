from math import log
from termcolor import colored
from re import search, IGNORECASE

from Nemesis.lib.Globals import Color
from Nemesis.lib.Globals import base64char, hexchar, dom_sources_regex, dom_sinks_regex
from Nemesis.lib.Globals import url_regex, url_regex_without_netloc, subdomain_regex, path_regex, single_path_regex
from Nemesis.lib.Globals import web_services_regex, custom_regex_sensitive, custom_regex_insensitive, experimental_path_regex

from warnings import warn
warn("Experimental path regex is experimental and might generate false positives")

def banner():
    b = '\x1b[1m\x1b[31m    _   __                         _     \n   / | / /__  ____ ___  ___  _____(_)____\n  /  |/ / _ \\/ __ `__ \\/ _ \\/ ___/ / ___/\n / /|  /  __/ / / / / /  __(__  ) (__  ) \n/_/ |_/\\___/_/ /_/ /_/\\___/____/_/____/  \n                                         \n\x1b[0m'
    print(b)

def starter(argv):
    from sys import stdin
    if argv.banner:
        banner()
        exit()
    if not argv.wordlist:
        if not argv.url:
            if not argv.stdin:
                print(f"{Color.bad} Use --help")
                exit()
            else:
                return (line.rstrip('\n').strip(' ') for line in stdin.read().split('\n') if line)
        else:
            return [argv.url.strip(' ')]
    else:
        return (line.rstrip('\n').strip(' ') for line in open(argv.wordlist) if line)

def shannon_entropy(data, iterator):
    if not data:
        return 0
    entropy = 0
    for val in iterator:
        p_x = float(data.count(val))/len(data)
        if p_x > 0:
            entropy += - p_x * log(p_x, 2)
    return float(entropy)

def reduce_string(word: str, args = []) -> str:
    if not word:
        return ""
    word = word.rstrip('//').rstrip(';')
    n = 0
    while len(args) > n:
        for arg in args:
            word = word.strip(arg)
        n += 1
    return word

def dom_source_extract(line: str) -> tuple:
    output_list = ()
    for dom_source in dom_sources_regex:
        if search(dom_source, line, IGNORECASE):
            mline = search(dom_source, line, IGNORECASE).group()
            output_list = (mline, 'dom_source_match')
    return output_list

def dom_sink_extract(line: str) -> tuple:
    output_list = ()
    for dom_sink in dom_sinks_regex:
        if search(dom_sink, line, IGNORECASE):
            mline = search(dom_sink, line, IGNORECASE).group()
            output_list = (mline, 'dom_sink_match')
    return output_list

def subdomain_extract(line: str, domain: str) -> tuple:
    output_list = ()
    subdomain = subdomain_regex(domain)
    if search(subdomain, line, IGNORECASE):
        mline = search(subdomain, line, IGNORECASE).group()
        if not mline == domain:
            output_list = (mline, 'subdomain_match')
    return output_list

def url_extract(line: str) -> tuple:
    output_list = ()
    for web_service in web_services_regex:
        if search(web_service, line):
            mline = search(web_service, line).group()
            output_list = (mline, 'web_services_match')
    if search(url_regex, line):
        mline = search(url_regex, line).group()
        output_list = (mline, 'url_match')
    elif search(url_regex_without_netloc, line):
        mline = search(url_regex_without_netloc, line).group()
        output_list = (mline, 'url_match_without_netloc')
        #if unender(unurler(line), '/') == self.argv.domain:
        #    return ()
    return output_list

def path_extract(line: str) -> tuple:
    output_list = ()
    if search(experimental_path_regex, line):
        mline = search(experimental_path_regex, line).group()
        output_list = (mline, 'experimental_path_match')
    elif search(path_regex, line):
        mline = search(path_regex, line).group()
        output_list = (mline, 'path_match')
    elif search(single_path_regex, line):
        mline = reduce_string(search(single_path_regex, line).group(), args=['"', "'"])
        output_list = (mline, 'single_path_match')
    return output_list

def shannon_extract(line: str) -> tuple:
    output_list = ()
    entropy = float(3.72)
    for word in line.split(' '):
        if len(word) > 5:
            if shannon_entropy(word, base64char) > entropy or shannon_entropy(word, hexchar) > entropy:
                word = reduce_string(word, args=['"', "'"])
                output_list = (word, 'shannon_entropy_match')
    return output_list

def custom_extract(line: str) -> tuple:
    output_list = ()
    for custom in custom_regex_sensitive:
        if search(custom, line):
            mline = search(custom, line).group()
            output_list = (mline, 'custom_regex')
    for custom in custom_regex_insensitive:
        if search(custom, line, IGNORECASE):
            mline = search(custom, line, IGNORECASE).group()
            output_list = (mline, 'custom_regex')
    return output_list

def link_extract(line: str, domain = "") -> tuple:
    # rename output_list to output_tuple
    output_list = ()
    if not line or line.startswith('#'):
        return output_list
    for web_service in web_services_regex:
        if search(web_service, line):
            mline = search(web_service, line).group()
            output_list = (mline, 'web_services_match')
            return output_list
    # url_regex over subdomain_regex, might supress
    if search(url_regex, line):
        mline = search(url_regex, line).group()
        output_list = (mline, 'url_match')
    elif search(url_regex_without_netloc, line):
        mline = search(url_regex_without_netloc, line).group()
        output_list = (mline, 'url_match_without_netloc')
    elif search(path_regex, line):
        mline = search(path_regex, line).group()
        output_list = (mline, 'path_match')
    elif search(single_path_regex, line):
        mline = search(single_path_regex, line).group()
        output_list = (mline, 'single_path_match')
    elif search(experimental_path_regex, line):
        mline = search(experimental_path_regex, 'experimental_path_match')
        output_list = (mline, 'experimental_path_match')
    elif domain and search(subdomain_regex(domain), line):
        mline = search(subdomain_regex(domain).group(), line)
        if not mline == domain:
            output_list = (mline, 'subdomain_match')
    return output_list

def pretty_print(line: str, match_type_tuple: tuple):
    if not match_type_tuple: return
    match, match_type = match_type_tuple
    match_type = match_type.split('_match')[0].replace('_', ' ')
    split_beginning, split_end = line.split(match)[0], line.split(match)[-1]
    colored_line = split_beginning + colored(match, color='red', attrs=['bold']) + split_end
    print(f"{Color.good} Found: {colored_line} (Match: {match_type})")