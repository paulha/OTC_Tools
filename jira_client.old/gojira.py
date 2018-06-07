from jira.client import JIRA
import itertools
import utility_funcs.logger_yaml as log

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
# Note: host_alias appears unused...
def init_jira(config={}):
    """
    Load Configuration from config.yaml
    
    Configuration may be held in either ~/.jira/config.yaml or ./config.yaml

    This is no longer compatible with previous config.yaml login configuration
    """
    auth = (config['username'], config['password'])
    host = config['host']
    server = {'server': host}
    if 'verify' in  config:
        verified = "verified"
        # Make certificate file relative to config file...
        config_directory = "" if 'config_directory' not in config else config['config_directory']
        server['verify'] = config_directory+'/'+config['verify']
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
        raise e

    return jira


# TODO: add a no_increment_start option to handle queries that reduce the
#       count of the result set
def jql_issue_gen(query, jira, show_status=False, count_change_ok=False):
    if not query:
        raise Exception('no query provided')

    if show_status:
        log.logger.info( "JQL: %s", query )

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
