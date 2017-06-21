from os.path import expanduser, pathsep
from jira.client import JIRA
import itertools
import yaml
import logger_yaml as log

from utility_funcs.search import get_server_info

CONFIG_FILE = './config.yaml'+pathsep+'~/.jira/config.yaml'


def chunker(iterable, n, fillvalue=None):
    "Return n at a time, no padding at end of list"
    
    # only need 2n items to cause x/n to cycle between 0 & 1,
    # marking a group
    r = range(n*2)
    rc = itertools.cycle(r)
    l = lambda x: rc.next() / n

    # ...and then strip off the group label
    return (i[1] for i in itertools.groupby(iterable, l))


# set up jira connection
def init_jira(host_alias = "jira-t3"):
    """
    Load Configuration from config.yaml
    
    Configuration may be held in either ~/.jira/config.yaml or ./config.yaml

    This is no longer compatible with previous config.yaml login configuration
    """
    config = get_server_info(host_alias, CONFIG_FILE)    # possible FileNotFoundError
    # -- Check for missing parameters:
    errors = 0
    if config is None:
        errors = 1
        log.logger.fatal("Configuration section for server %s is missing." % (host_alias))
        exit(-1)
    if 'username' not in config:
        errors += 1
        log.logger.fatal("username for server %s is missing." % (host_alias))
    if 'password' not in config:
        errors += 1
        log.logger.fatal("password for server %s is missing." % (host_alias))
    if 'host' not in config:
        errors += 1
        log.logger.fatal("host url for server %s is missing." % (host_alias))
    if errors > 0:
        log.logger.fatal("configuration errors were found, exiting." )
        exit(-1)

    auth = (config['username'], config['password'])
    host = config['host']
    server = {'server': host}
    if 'verify' in  config:
        verified = "verified"
        server['verify'] = config['verify']
    else:
        verified = "unverified"
        # -- Following code is supposed to ignore a certificate error, but it doesn't. :-(
        import requests
        from requests.packages.urllib3.exceptions import InsecureRequestWarning
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    # Connect to JIRA
    try:
        log.logger.info( "Connecting to %s using %s connection.", host, verified)
        jira = JIRA(server, basic_auth=auth)
    except Exception as e:
        log.logger.fatal( e, exc_info=True )
        log.logger.fatal( "Failed to connect to JIRA." )
        exit(0)

    return jira


# TODO: add a no_increment_start option to handle queries that reduce the
#       count of the result set
def jql_issue_gen(query, jira, show_status=False, count_change_ok=False):
    if not query:
        raise Exception('no query provided')

    if show_status:
        log.logger.info( "JQL:", query )

    seen = 0
    startAt = 0
    total = None
    while 1:
        issues = jira.search_issues(query, startAt=startAt)

        if len(issues) == 0:
            if show_status:
                log.logger.info( "loaded all %d issues"%total )
            break

        if total is None:
            total = issues.total
        elif total != issues.total and not count_change_ok:
            raise Exception('Total changed while running %d != %d'%(total, issues.total))

        for i in issues:
            yield i

        seen += len(issues)
        if show_status:
            log.logger.info( "loaded %d issues starting at %d, %d/%d"%(len(issues), startAt, seen, total) )
        startAt += len(issues)


def issue_keys_issue_gen(issue_key_list, jira, show_status=False, group_len=20):
    if not issue_key_list:
        raise Exception('no issues provided')

    jql = "key in ( {} )"

    key_groups = chunker(issue_key_list, group_len)
    jqls = (jql.format(" , ".join(key_group)) for key_group in key_groups)

    jql_gens = (jql_issue_gen(j, jira, show_staus=show_status) for j in jqls)
    return itertools.chain.from_iterable(jql_gens)
