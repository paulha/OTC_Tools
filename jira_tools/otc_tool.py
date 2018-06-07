from os.path import expanduser, pathsep, dirname, realpath
import argparse
import sys
# from gojira import init_jira, jql_issue_gen, issue_keys_issue_gen
# from jirafields import make_field_lookup
from jira_class import Jira, get_query, init_jira, jql_issue_gen, make_field_lookup

# -- todo: Uncomfortable for two different imports from the same module to be handled differently...
from utility_funcs.search import get_server_info, search_for_profile
import utility_funcs.logger_yaml as log

from copy_platform_to_platform import copy_platform_to_platform
from add_label_to_platform_version import add_label_to_platform_version
from dng_vs_jira_find_added import find_added_dng_vs_jira
from areq_superseded_by_preq import areq_superceded_by_preq
from label_from_labeled_items import LabelFromLabeledItems
from project_to_csv import ProjectToCSV
from time import strftime

LOG_CONFIG_FILE = 'logging.yaml'+pathsep+dirname(realpath(sys.argv[0]))+'/logging.yaml'
CONFIG_FILE = dirname(realpath(sys.argv[0]))+'/config.yaml'+pathsep+'~/.jira/config.yaml'
QUERIES_FILE = dirname(realpath(sys.argv[0]))+'/queries.yaml'+pathsep+'~/.jira/queries.yaml'
SCENARIO_FILE = 'scenarios.yaml'+pathsep+dirname(realpath(sys.argv[0]))+'/scenarios.yaml'

log_file = log.logging.getLogger("file")

#AND_VER = "O"
#PLATFORM = 'Broxton-P IVI"'
#droid_ver_id = 'customfield_10811'


## from the create_efeature_add_dessert
#            if target_dessert: ### TODO NOT WORKING TODO NOT WORKING TODO ###
#                # if a new dessert letter is passed, navigate the parent subtask-list for each source child's parent
#                find_parent = "key = %s"%parent_key
#                parent_feature = j.search_issues("key=%s"%issue.fields.parent.key, 0)[0]
#                parent_subtasks = list(parent_feature.fields.subtasks)
#
#                dupe_list = []
#                for subtask in parent_subtasks:
#                    find_subtask_dessert = "key = %s"%subtask.key
#                    subtask_info = j.search_issues(find_subtask_dessert, 0)[0]
#                    subtask_dessert_version = getattr(subtask_info.fields, and_vers_key)[0].value
#                    if (subtask_dessert_version == "O"):
#                        this_issue_prio = [{'issue_id': issue.key, 'parent_id': issue.fields.parent.key, 'clone_id': subtask.key, 'pri_name': issue.fields.priority.name, 'pri_id': issue.fields.priority.id}]
#                        dupe_list.append(subtask_info.key)
#                        # create dupe list
#                if dupe_list:
#                    doing_list += [{'source_id': issue.key, 'summary': 'dupe;no-clone'}]
#                    log.logger.info( "already got %s"%issue.key )
# def create_from_jql(j):
#     i = 0
#
#     fl = make_field_lookup(j)
#     and_vers_key = fl.reverse('Android Version(s)')
#     platprog_key = fl.reverse('Platform/Program')
#
#     #jql = """project = CREQ AND issuetype = Feature AND assignee = swmckeox"""
#     jql = """project = %s AND issuetype = Feature"""%(PROJECT,)
#     for areq in jql_issue_gen(jql, j):
#         log.logger.info(areq.key, areq.fields.summary, getattr(areq.fields, and_vers_key)[0].value)
#
#         for platprog in getattr(areq.fields, platprog_key):
#             # Create Sub-task
#             i += 1
#             and_ver = getattr(areq.fields, and_vers_key)[0].value
#
#             ### Nerfed for safety
#             # log.logger.info( i, areq.key, platprog.value )
#             # efeature=create_e_feature_from_feature(j, areq, ASSIGNEE, VAL_LEAD, and_ver, platprog.value)
#             # new_sum = efeature.fields.summary.replace('[]', '[4.4]')
#             # efeature.update(fields={'summary':new_sum})
#             # log.logger.info( "\t", efeature.key,efeature.fields.summary, getattr(efeature.fields, and_vers_key)[0].value )
#             # log.logger.info( "\t", efeature.key,efeature.fields.summary, getattr(efeature.fields, and_vers_key)[0].value )
#

def add_value_to_list(issue, key, new_value):
    values = [x.value for x in getattr(issue.fields, key)]
    if new_value not in values:
        values.append(new_value)
        update = [{'value':v} for v in values]
        issue.update(fields = {key: update})


def ensure_parent_feature(jira, issue):
    if issue.fields.issuetype.name == 'E-Feature':
        feature_key = issue.fields.parent.key
        feature = jira.issue(feature_key)
    elif issue.fields.issuetype.name != 'Feature':
        key = issue.key
        itype = issue.fields.issuetype.name
        msg = '{} is a {}, not a Feature or E-Feature'.format(key, itype)
        raise Exception(msg)
    else:
        feature = issue
    return feature


def create_e_feature_from_feature(jira, feature, assignee, val_lead, and_ver, platform):
    fl = make_field_lookup(jira)
    val_lead_key = fl.reverse('Validation Lead')
    and_vers_key = fl.reverse('Android Version(s)')
    platprog_key = fl.reverse('Platform/Program')

    new_efeature_dict = {
            'project': {'key': feature.fields.project.key},
            'parent': {'key': feature.key},
            'summary': 'TBD',
            'issuetype': {'name': 'E-Feature'},
            'assignee': {'name': assignee},
            val_lead_key: {'name': val_lead},
            and_vers_key: [{'value': and_ver}],
            platprog_key: [{'value': platform}]
    }

    efeature = jira.create_issue(fields=new_efeature_dict)
    return efeature


def create_from_efeature_key_list(j, filename):
    create_count = 0

    fl = make_field_lookup(j)
    platprog_key = fl.reverse('Platform/Program')
    and_vers_key = fl.reverse('Android Version(s)')

    source_issue_keys = ( line.strip() for line in open(filename) if line.strip() )

    for source_issue in issue_keys_issue_gen(source_issue_keys, j):
        log.logger.info("-" * 40)
        log.logger.info(source_issue.key, source_issue.fields.summary)

        feature = ensure_parent_feature(j, source_issue)

        log.logger.info(feature.key, feature.fields.summary)

        add_value_to_list(feature, platprog_key, NEW_PLATFORM)
        efeature = create_e_feature_from_feature(jira, feature, ASSIGNEE, VAL_LEAD, AND_VER, NEW_PLATFORM)

        create_count += 1
        log.logger.info(efeature.key, efeature.fields.summary, getattr(efeature.fields, and_vers_key))

    log.logger.info("created {} new e-features".format(create_count))


def add_dessert(j, jql, dessert):
    update_count = 0

    fl = make_field_lookup(j)
    and_vers_key = fl.reverse('Android Version(s)')


    for issue in jql_issue_gen(jql, j, count_change_ok=True):
        log.logger.info(issue.key)
        add_value_to_list(issue, and_vers_key, 'O')
        update_count += 1

    log.logger.info("Updated {} issues".format(update_count))


def clone_efeature_add_dessert(jira, jira_query, doing_list, target_platform, target_dessert, unassign_new):
    update_count = 0
    fl = make_field_lookup(jira)
    val_lead_key = fl.reverse('Validation Lead')
    and_vers_key = fl.reverse('Android Version(s)')
    platprog_key = fl.reverse('Platform/Program')
    exists_on = fl.reverse('Exists On')

    # get the initial list of source issues and iterate
    for issue in jql_issue_gen(jira_query, jira, count_change_ok=True):
        # TODO set up more logging
        # TODO set up more error handling for things like inactive users
        # TODO encapsulate in such a way that in the future this script should have separate functions to support:
        # * same platform, new dessert
        # * same dessert, new platform
        # current flow is: start with source child -> get to parent by ID -> get parent metadata and cut new e-feature into new platform
        try:
    
            # capture some info from each issue as it gets iterated over
            parent_key = issue.fields.parent.key
            doing_list += [{'parent': parent_key, 'source_child': issue.key, 'summary': issue.fields.summary}]
            # the new e-features should hit this as TRUE if the AREQ requester defined this as an SD;NP: request
            if target_platform:
                child_platform = target_platform
            else: # new e-features should hit this as FALSE if the AREQ requester defined this as an SP;ND: request
                child_platform = getattr(issue.fields, platprog_key)[0].value

            # Note: This looks like a tangiential issue not strictly related to the close...
            # set the assignee
            if issue.fields.assignee.name == 'danunora':
                target_assign = 'daqualls'
            elif issue.fields.assignee.name == 'etang1':
                target_assign = 'daqualls'
            elif issue.fields.assignee.name == 'atena':
                target_assign = 'daqualls' 
            else:
                target_assign = issue.fields.assignee.name
        
            if target_dessert == "":
                child_dessert = getattr(issue.fields, and_vers_key)[0].value

            # Note: These are the values for the record to be created...
            if True: ### TODO ALL SHOULD CURRENTLY GO THIS ROUTE AS OF 21MAR2017 TODO ###
                new_efeature_dict = {
                    'project': {'key': issue.fields.project.key},
                    'parent': {'key': issue.fields.parent.key},
                    'summary': issue.fields.summary,
                    'issuetype': {'name': 'E-Feature'},
                    'assignee': {'name': target_assign},
                    and_vers_key: [{'value': child_dessert}],
                    platprog_key: [{'value': child_platform}],
                    exists_on: [{'value': 'BXT-Joule'}]
                }

            log.logger.info( "creating new clone of %s" % issue.key )
            # fixme: This  doesn't seem right -- would try to create result from new_efeature_dict,
            #        even if it was left over from the previous iteration...
            efeature = jira.create_issue(fields=new_efeature_dict)
            update_count += 1
        except:
            log.logger.exception('cloning process halted and caught fire on issue %s' % issue.key)
            doing_list += [{'error_issue': issue.key, 'error_text': sys.exc_info()[0]}]
            log.logger.error("caught exception while cloning %s" % issue.key)
            return doing_list
 
    log.logger.info( "Updated {} issues".format(update_count) )
    return doing_list

# def dump_parent_info(jira, search_query, doing_list, target_platform, target_dessert, unassign_new):
#     fl = make_field_lookup(jira)
#     val_lead_key = fl.reverse('Validation Lead')
#     and_vers_key = fl.reverse('Android Version(s)')
#     platprog_key = fl.reverse('Platform/Program')
#     exists_on = fl.reverse('Exists On')
#
#     # get the initial list of source issues and iterate
#     for issue in jql_issue_gen(search_query, jira, count_change_ok=True):
#         # capture some info from each issue as it gets iterated over
#         parent_key = issue.fields.parent.key
#         find_parent = "key = %s" % parent_key
#         parent_feature = jira.search_issues("key=%s" % issue.fields.parent.key, 0)[0]
#         parent_subtasks = list(parent_feature.fields.subtasks)
#         log.logger.info("trying %s" % parent_key)
#         try:
#             parent = jira.search_issues(find_parent, 0)[0]
#             p_plats = []
#             p_plats += getattr(parent.fields, platprog_key)
#             log.logger.info(p_plats)
#             for plat in p_plats:
#                 ICL_found = 0
#                 if plat.value == "Icelake-U SDC":
#                     ICL_found += 1
#
#                 if ICL_found:
#                     log.logger.info("ICL num check TRUE")
#                 else:
#                     doing_list += [{'key': parent.key}]
#
#         except:
#             log.logger.error("ISSUE ERROR!")
#             doing_list += [{'error hit inside dump_parent_info sub-issue search': issue.key}]
#             continue
#
#
#     return doing_list

#============= Retired Code =======================================================
# def compare_priorities( args, config ):
#     jira = init_jira( args.name, config )
#     test_jql = """key = AREQ-23610"""
#     done_list = []
#
#     test_jql = """key = AREQ-23610"""
#     done_list = []
#
#     # get input from cmd line - TODO to be used for direction to either New Platform or New Dessert functions later
#     #    parser = argparse.ArgumentParser(description='Use this weird trick to save 600% time on cutting your *NEW* Android Requirement E-Features from home and make $7253 a month that insurance companies in OREGON don\'t want YOU to know!!')
#     #    parser.add_argument('-i','--input', help='Input file name',required=False)
#     #    args = parser.parse_args()
#
#     # SDNP = same dessert; new platform / SPND = same platform; new dessert
#     # set this according to AREQ request using cmd line args above
#     hasNewPlatform = False
#     hasNewDessert = False
#     if hasNewPlatform:
#         target_platform = "Broxton"
#         target_dessert = ""
#     if hasNewDessert:
#         target_platform = ""
#         target_dessert = "O"
#     else:
#         target_platform = ""
#         target_dessert = ""
#         #    dustin_jql = """project = AREQ AND "Platform/Program" = "Icelake-U SDC" AND issuetype = E-Feature AND priority != P4-Low ORDER BY priority ASC"""
#     amy_jql = """project = "Platforms Requirements" AND "Platform/Program" = "Icelake-U SDC" ORDER BY "Global ID" ASC"""
#     #    completed = dump_parent_info(jira, amy_jql, done_list, target_platform, target_dessert, True)
#     completed = compare_prios(jira, amy_jql, done_list)
#     filename = "17APR1427_AREQ-24084.txt"
#     thefile = open('%s' % filename, 'w')
#     for item in completed:
#         thefile.write("%s\n" % item)
#======================================================================================


def dump_parents(parser, args, config, queries ):
    #
    # -- What's the actual goal of this?
    #
    if dump_parents.__name__ not in queries:
        log.logger.fatal( "Query section for %s is missing: %s", dump_parents.__name__, queries)
        exit(-1)

    items=queries[dump_parents.__name__]

    # -- Make sure search query is defined
    if 'search' not in items:
        log.logger.fatal( "Search query for %s.search is missing: %s", dump_parents.__name__, queries)
        exit(-1)

    # -- Get and format it:
    search_query = items['search'].format_map(vars(args))
    log.logger.debug( "search query is: %s", search_query)

    # -- Make sure the match query is defined. (Don't fill it out yet though...)
    if 'match' not in items:
        log.logger.fatal( "Search query for %s.match is missing: %s", dump_parents.__name__, queries)
        exit(-1)
    match_query=items['match']
    log.logger.debug( "Match query is: %s", match_query)

    done_list = []

    jira = init_jira(config)

    field_lookup = make_field_lookup(jira)
    val_lead_key = field_lookup.reverse('Validation Lead')
    and_vers_key = field_lookup.reverse('Android Version(s)')
    platprog_key = field_lookup.reverse('Platform/Program')
    gid_finder = field_lookup.reverse('Global ID')

    for issue in jql_issue_gen(search_query, jira, count_change_ok=True):
        log.logger.info("Issue %s: %s", issue.key, issue.fields.summary)

        # -- Guarded access to parent key (may not exist!)
        try:
            parent_key = issue.fields.parent.key

        except AttributeError as e:
            log.logger.error("Exception %s: Results of the query '%s' do not have a 'parent' field.", e, search_query)
            return

        # -- fill out the match search
        temp_dict = {'key': parent_key}     # What we're really looking for...
        temp_dict.update(vars(args))        # other values that might be useful in a complex query
        find_parent = match_query.format_map(temp_dict)
        log.logger.debug("match query is: %s", find_parent)

        try:
            parent = jira.search_issues(find_parent, 0)[0]
            p_plats = []
            p_plats += getattr(parent.fields, platprog_key)
            log.logger.debug(p_plats)
            # todo: Make Generic! (I'm not clear on exactly what this is trying to do...)
            # Looks like this is finding the cases where Icelake is NOT found in p_plats
            #
            #   Note:   This is odd because you should be able to use
            #
            #               if "Icelake-U SDC" not in p_plats:
            #                   log.logger.info( "New      -- Icelake not in %s", parent.key )
            #
            #           but it doesn't work correctly in the case where there's only
            #           a single "Icelake-U SDC" entry in p_plats. It always returns
            #           True in that case, instead of the correct False.
            #

            # todo: Make Generic! (I'm not clear on exactly what this is trying to do...)
            ICL_NOT_found = True
            for plat in p_plats:
                log.logger.debug( "plat is '%s'", plat)
                ICL_NOT_found = False if "Icelake-U SDC" == plat.value else ICL_NOT_found

            if ICL_NOT_found:
                log.logger.info("Icelake not in %s", parent.key)
                done_list += [{'key': parent.key}]
                old_printed=True

        except Exception as e:
            log.logger.error("ISSUE ERROR! %s", e)
            done_list += [{'error hit inside dump_parent_info sub-issue search': issue.key}]
            continue

    # -- Dump the output file
    with open(args.output,'w') as outfile:
        for item in done_list:
            outfile.write("%s\n" % item)


def compare_priorities(parser, args, config, queries):
    if compare_priorities.__name__ not in queries:
        log.logger.fatal( "Query section for %s is missing: %s", dump_parents.__name__, queries)
        exit(-1)

    items=queries[compare_priorities.__name__]

    # -- Make sure search query is defined
    if 'search' not in items:
        log.logger.fatal( "Search query for %s.search is missing: %s", compare_priorities.__name__, queries)
        exit(-1)

    # -- Get and format it:
    search_query = items['search'].format_map(vars(args))
    log.logger.debug( "search query is: %s", search_query)

    # -- Make sure the match query is defined. (Don't fill it out yet though...)
    if 'match' not in items:
        log.logger.fatal( "Search query for %s.match is missing: %s", dump_parents.__name__, queries)
        exit(-1)
    match_query=items['match']
    log.logger.debug( "Match query is: %s", match_query)

    done_list = []

    jira = init_jira(config)

    field_lookup = make_field_lookup(jira)
    val_lead_key = field_lookup.reverse('Validation Lead')
    and_vers_key = field_lookup.reverse('Android Version(s)')
    platprog_key = field_lookup.reverse('Platform/Program')
    gid_finder = field_lookup.reverse('Global ID')

    for issue in jql_issue_gen(search_query, jira, count_change_ok=True):
        log.logger.info("Issue %s: %s", issue.key, issue.fields.summary)
        gid = getattr(issue.fields, gid_finder)
        log.logger.debug( "trying %s"%gid )

        # -- substitute in the gid at the last moment...
        temp_dict = {'gid': gid}            # What we're really looking for...
        temp_dict.update(vars(args))        # other values that might be useful in a complex query
        query = match_query.format_map(temp_dict)
        log.logger.debug("match query is: %s", query)
        try:
            matches = jira.search_issues(query, 0)
            if isinstance(matches, object) and len(matches)>0:
                match = matches[0]
                id1 = match.fields.priority.id
                id2 = issue.fields.priority.id
                if id1 == id2:
                    log.logger.debug("priority match")
                else:
                    log.logger.debug("priority mismatch")
                    done_list += [{'key': issue.key, 'pri': match.fields.priority.name}]
            else:
                log.logger.info("No match found! -- %s", query)
                done_list += [{'no match': issue.key}]

        except Exception as e:
            # No errors should happen now...
            log.logger.warn("Error occured processing issue -- %s %s", e.__class__, e.__cause__)
            continue

    with open(args.output,'w') as outfile:
        for item in done_list:
            outfile.write("%s\n" % item)


def query_one_item(jira, item_query, param_dict):
    formatted_query = item_query.format_map(param_dict)
    log.logger.debug("get_one_item formatted_query is: %s", formatted_query)
    item = None
    try:
        item = jira.search_issues(formatted_query, 0)
        if isinstance(item, list) and len(item) > 0:
            item = item[0]
            log.logger.debug("\tget_one_item item found: %s: %s", item.key, item.fields.summary)
        else:
            item = None
            log.logger.debug("No item found for query '%s'!", formatted_query)

    except Exception as e:
        # No errors should happen now...
        log.logger.warn("Error occured processing issue -- %s %s", e.__class__, e.__cause__)

    # -- parent_feature containst the parent or is None.
    return item


def is_this_the_same_feature(parent_feature, source_e_feature, target_e_feature):
    """Compare: is target_e_feature a copy of the parent Feature?"""
    errors=[]
    if parent_feature.fields.description != target_e_feature.fields.description:
        errors += ["Descriptions don't match"]

    if parent_feature.fields.summary not in target_e_feature.fields.summary:
        errors += ["Feature summary not contained in E-Feature"]

    if source_e_feature.fields.assignee != target_e_feature.fields.assignee:
        errors += ["Source E-Feature assignee %s not contained in E-Feature assignee %s" \
                        % (source_e_feature.fields.assignee.name, target_e_feature.fields.assignee.name)]
    if errors:
        raise ValueError([errors])
    return True


def e_feature_scanner(parser, scenario, config, search, queries):
    """AREQ-24757: Create O-MR1 dessert AREQ eFeatures for BXT-P IVI based on O dessert

    Attributes:
        parser (argparse.ArgumentParser): Can be used for option specific parsing of arguments.
        scenario (Dict): Dictionary like list of arguments and values from the command line. NOT iterable!
        config (YAML): Hierarchical list of configuration settings based on server name command argument
        queries (YAML): Also a hierarchical list of queries to use...

    Processing:
        * For each AREQ eFeature by this JQL query:
                project = AREQ AND issuetype = E-Feature AND status in (Open, "In Progress", Closed, Merged, Blocked)
                            AND "Android Version(s)" in (O) AND "Platform/Program" in ("Broxton-P IVI")
            - If there is NOT an O-MR1 dessert eFeature mapping to the same Parent:

                * Clone the existing "O" **feature** entry (not the e-feature!)
                * set state to "OPEN"
                * set android version(s) to "O-MR1"
                * (Be sure that Priority, Owner, Exists On are set from the (existing) "O" version of the e-feature.
                   Note that most of these fields should copy from the Feature, even though we're createing an
                   e-feature!)
                * Set title to the O-MR1 dessert version format
                * Save and link to the parent feature

    Note:
        * In verify mode:
            - If sibling_e_feature is found, then it should be compared to the parent_feature from which it
              should have been cloned
            - If sibling_e_feature is NOT found, there is a missing entry which should be logged.

        * In update mode:
            - If sibling_e_feature is found, then update can be short circuited
            - If sibling_e_feature is NOT found, there is a missing entry which should be created.


    :return: Nothing on success, exits on error.
    """
    if e_feature_scanner.__name__ not in queries:
        log.logger.fatal( "Query section for %s is missing: %s", e_feature_scanner.__name__, queries)
        exit(-1)

    candidate_efeatures_query = get_query('candidate_e-features', queries, e_feature_scanner.__name__, params=scenario, log=log)
    parent_query = get_query('parent_query', queries, e_feature_scanner.__name__, log=log)
    sibling_query = get_query('sibling_query', queries, e_feature_scanner.__name__, log=log)

    log.logger.info("Examining source platform {splatform}, source android version {sversion}, target android version {tversion}".format_map(scenario))

    verify = scenario['verify']
    update = scenario['update']
    # rename = scenario['rename']
    log.logger.info("Verify is %s, and Update is %s", verify, update)
    log.logger.info("=================================================================")

    # -- Get and format it:
    jira = Jira(scenario['name'], search, log=log.logger)

    field_lookup = make_field_lookup(jira)
    and_vers_key = field_lookup.reverse('Android Version(s)')
    platprog_key = field_lookup.reverse('Platform/Program')
    exists_on = field_lookup.reverse('Exists On')
    verified_on = field_lookup.reverse('Verified On')
    failed_on = field_lookup.reverse('Failed On')
    blocked_on = field_lookup.reverse('Blocked On')
    tested_on = field_lookup.reverse('Tested On')

    features_scanned = 0
    update_count = 0
    verify_failures = 0
    update_failures = 0
    processing_errors = 0
    for current_e_feature in jira.do_query(candidate_efeatures_query):
        features_scanned += 1
        parent_feature = None
        log.logger.info("Checking on E-Feature %s: %s", current_e_feature.key, current_e_feature.fields.summary)

        # -- OK so now we have found the source e-feature. We want to get its parent
        param_dict = {'parent_key': current_e_feature.fields.parent}   # What we're really looking for...
        param_dict.update(scenario)                                    # other values that might be useful in a complex query

        # -- Check for duplicate sibling feature, if found no need to create a new one.
        sibling_e_feature = query_one_item(jira.jira_client, sibling_query, param_dict)
        # sibling_e_feature = jira.get_item(key=current_e_feature.fields.parent.key)
        if sibling_e_feature is not None:
            # -- Sibling already exists
            if update:
                # -- no need to output a E-Feature
                log.logger.debug("Sibling to E-Feature already exists, no need to create it: %s %s", sibling_e_feature.key, sibling_e_feature.fields.summary)

            if verify:
                # -- Look up the parent, to make a comparison
                # parent_feature = query_one_item(jira, parent_query, param_dict)
                parent_feature = jira.get_item(key=sibling_e_feature.fields.parent.key)
                if parent_feature is None:
                    # -- Sibling without parent
                    log.logger.warning("E-Feature %s has no parent", current_e_feature.key)
                    processing_errors += 1

                # -- compare the found sibling to the parent, output on compare fail...
                try:
                    is_this_the_same_feature(parent_feature, current_e_feature, sibling_e_feature)
                except ValueError as e:
                    log.logger.error("E-Feature %s does not match Feature %s. Exception '%s'",
                                     sibling_e_feature.key, parent_feature.key, e)
                    verify_failures += 1

            continue

        # parent_feature = query_one_item(jira, parent_query, param_dict)
        if parent_feature is None:
            parent_feature = jira.get_item(key=current_e_feature.fields.parent.key)

        if parent_feature is None:
            # -- Sibling without parent
            log.logger.warning("E-Feature %s has no parent", current_e_feature.key)
            processing_errors += 1
            continue

        # -- Note: Code to fill out new sibling goes here.
        if not update:
            # -- Missing E-Feature:
            log.logger.warning("An E-Feature is missing. {tplatform} version {tversion}. Parent Feature is %s. Version {sversion} E-Feature is %s %s %s"
                               .format_map(scenario),
                               parent_feature.key, current_e_feature.key,
                               current_e_feature.fields.customfield_11700[0],   # TODO: WHAT?  getattrib()?
                               current_e_feature.fields.summary)                # TODO: getattrib()?
            verify_failures += 1

        if update:
            log.logger.warning("Creating E-Feature {splatform} version {tversion} for Feature %s: %s".format_map(scenario),
                            parent_feature.key, parent_feature.fields.summary)
            # Note: This is special code making Dustin the assignee for three other possible assignees.
            try:
                if current_e_feature.fields.assignee is None:
                    # -- if it's unassigned, leave it that way
                    log.logger.debug("Assigning new e-feature to None (is that valid?)")
                    target_assign = None
                elif current_e_feature.fields.assignee.name in ['danunora', 'etang1', 'atena']:
                    # -- Change assignee to Dustin
                    log.logger.debug("Assigning new e-feature to 'daqualls'")
                    target_assign = 'daqualls'
                else:
                    # -- It's assigned to someone else, leave it that way.
                    target_assign = current_e_feature.fields.assignee.name
            except Exception as e:
                # -- Something happened; log the error and continue.
                log.logger.error(e, exc_info=True)

            # -- Creating an E-Feature (sub-type of Feature) causes appropriate fields of the parent Feature
            #    to be copied into the E-Feature *automatically*.
            new_e_feature_dict = {      # TODO: getattrib()!
                'project': {'key': parent_feature.fields.project.key},
                'parent': {'key': parent_feature.key},
                'summary': parent_feature.fields.summary,
                'issuetype': {'name': 'E-Feature'},
                'assignee': {'name': target_assign},
                and_vers_key: [{'value': scenario['tversion']}],
                platprog_key: [{'value': scenario['splatform']}],
            }

            log.logger.debug("Creating E-Feature clone of Feature %s -- %s" % (parent_feature.key, new_e_feature_dict))

            # -- Having created the issue, now other fields of the E-Feature can be updated:
            def _define_update(update_list, field, entry):
                update_list[field] = [{'value': x.value} for x in getattr(entry.fields, field)] \
                                                if getattr(entry.fields, field) is not None else []

            update_fields = {
                'priority': {'name': 'P1-Stopper'},
                'labels': [x for x in getattr(current_e_feature.fields, 'labels')]
            }
            _define_update(update_fields, exists_on, current_e_feature)
            _define_update(update_fields, verified_on, current_e_feature)
            _define_update(update_fields, failed_on, current_e_feature)
            _define_update(update_fields, blocked_on, current_e_feature)
            _define_update(update_fields, tested_on, current_e_feature)

            sibling_e_feature = jira.create_issue(fields=new_e_feature_dict)
            sibling_e_feature.update(notify=False, fields=update_fields)
            # jira.clone_e_feature_from_parent(parent_feature.fields.summary, parent_feature,
            #                                  scenario, sibling=sibling_e_feature, log=log)

            # # -- TODO: What about attachments? Something like this, maybe
            # for attachment in current_e_feature.fields.attachment:
            #     content = attachment.get()  # Could be memory intensive...
            #     import StringIO
            #     new_attachment = StringIO.StringIO()
            #     new_attachment.write(data)
            #     jira.add_attachment(issue=sibling_e_feature, attachment=new_attachment, filename=attachment.filename)

            # -- It would be possible to copy the *content* of comments from the source record,
            #    but the details of the date and author would be lost.
            # x = jira.jira_client.comments(current_e_feature)
            jira.jira_client.add_comment(sibling_e_feature,
                                         """This E-Feature was created by {command}.
            
                                         Parent Feature is %s and source E-Feature is %s.
                                         
                                         For previous comments and attachments, refer to %s
            
                                         %s""".format_map(scenario)
                                         % (parent_feature.key, current_e_feature.key, current_e_feature.key,
                                            scenario['comment'] if scenario['comment'] is not None else ""))

            update_count += 1

            # todo: what was this? --- jira.add

            # -- Validate that the create and update actually worked! :-)
            try:
                is_this_the_same_feature(parent_feature, current_e_feature, sibling_e_feature)
            except ValueError as e:
                log.logger.error("Created E-Feature %s does not match Feature %s. Exception '%s'",
                                 sibling_e_feature.key, parent_feature.key, e)
                update_failures += 1

            if scenario['createmax'] and update_count>=scenario['createmax']:
                break

    log.logger.info("-----------------------------------------------------------------")
    log.logger.info("%s source E-Feature(s) were considered. ", features_scanned)

    if verify:
        log.logger.info("%s E-Feature comparison failure(s). ", verify_failures)

    if update:
        log.logger.info("%s new E-Feature(s) were created, %s update failures. ", update_count, update_failures)

    log.logger.info("%s processing error(s). ", processing_errors)

# -- https://jira01.devtools.intel.com/browse/AREQ-24748
def scan_areq_and_check_for_preq(parser, scenario, config, queries):
    """

    Hi Hanchett, PaulX - Please create a script / query comparing
    the Icelake-U SDC AREQs with the label "IOTG_IVI" associated
    to them and ensure that each one has a PREQ linked to it.
    Thanks! Amy

    Hi Hanchett, PaulX - If you do a query in JIRA, there are a
    set of IceLake-U SDC e-features that have the label "IOTG_IVI"
    associated with them. I would like for you to check that each
    of these AREQs has a PREQ linked to it. Please let me know the
    list of AREQs that do not have a PREQ linked to them (from the
    sub-set of AREQs that have the IOTG_IVI label associated with
    them).
    Thanks! Amy

    """
    if scan_areq_and_check_for_preq.__name__ not in queries:
        log.logger.fatal( "Query section for %s is missing: %s", e_feature_scanner.__name__, queries)
        exit(-1)

    items=queries[scan_areq_and_check_for_preq.__name__]

    # -- Make sure search query is defined
    if 'candidate_entries' not in items:
        log.logger.fatal( "Search query for %s.search is missing: %s", 'candidate_entries', queries)
        exit(-1)

    # -- Get and format it:
    candidate_entries_query = items['candidate_entries'].format_map(scenario)
    log.logger.debug( "search query is: %s", candidate_entries_query)

    if 'target_entry' not in items:
        log.logger.fatal( "Target query for %s.search is missing: %s", 'target_entry', queries)
        exit(-1)

    target_query = items['target_entry']
    log.logger.debug( "target query is: %s", target_query)

    log.logger.info("Examining source platform {splatform}, source android version {sversion}, target android version {tversion}".format_map(scenario))

    verify = scenario['verify']
    update = scenario['update']
    log.logger.info("Verify is %s and Update is %s", verify, update)
    log.logger.info("=================================================================")

    # -- Get and format it:
    jira = init_jira(config)

    field_lookup = make_field_lookup(jira)
    and_vers_key = field_lookup.reverse('Android Version(s)')
    platprog_key = field_lookup.reverse('Platform/Program')
    exists_on = field_lookup.reverse('Exists On')

    features_scanned = 0
    warnings_issued = 0
    verify_failures = 0
    update_failures = 0
    processing_errors = 0
    for current_entry in jql_issue_gen(candidate_entries_query, jira, count_change_ok=True):
        features_scanned += 1
        log.logger.debug("Checking on entry %s: %s", current_entry.key, current_entry.fields.summary)

        preqs = {}

        def do_lookup(key, query):
            param_dict = {'key': key}  # What we're really looking for...
            param_dict.update(scenario)  # other values that might be useful in a complex query
            return query_one_item(jira, query, param_dict)

        for link in current_entry.fields.issuelinks:
            try:
                key = link.outwardIssue.key
                log.logger.debug("outward key is %s", key)
                target_entry = do_lookup(key, target_query)
                if target_entry is not None:
                    preqs[key] = preqs[key] + 1 if key in preqs else 1
                    if "IOTG_IVI" not in target_entry.fields.links :
                        log.logger.info("For item %s, referenced entry %s does not have label %s",
                                            current_entry.key, target_entry.key, "IOTG_IVI")
                        warnings_issued += 1
                    log.logger.debug("found %s", target_entry)

            except AttributeError as e:
                pass

            try:
                key = link.inwardIssue.key
                log.logger.debug("inward key is %s", key)
                target_entry = do_lookup(key, target_query)
                if target_entry is not None:
                    preqs[key] = preqs[key] + 1 if key in preqs else 1
                    if "IOTG_IVI" not in target_entry.fields.links :
                        log.logger.info("For item %s, referenced entry %s does not have label %s",
                                            current_entry.key, target_entry.key, "IOTG_IVI")
                    warnings_issued += 1
                    log.logger.debug("found %s", target_entry)

            except AttributeError as e:
                pass

        if len(preqs) == 0:
            warnings_issued += 1
            log.logger.warning("For item %s, No PREQs were found.", current_entry.key)
        elif len(preqs) > 1:
            warnings_issued += 1
            log.logger.warning("For item %s, MULTIPLE PREQ's (%s) were found.", current_entry.key, preqs.keys())

    log.logger.info("-----------------------------------------------------------------")
    log.logger.info("%s source entries were considered. ", features_scanned)
    log.logger.info("%s warnings were issued. ", warnings_issued)
    log.logger.info("")

    # if verify:
    #     log.logger.info("%s E-Feature comparison failure(s). ", verify_failures)
    #
    # if update:
    #     log.logger.info("%s new E-Feature(s) were created, %s update failures. ", update_count, update_failures)

    log.logger.info("%s processing error(s). ", processing_errors)


def main():
    log.setup_logging(LOG_CONFIG_FILE,
                      # override={'handlers': {'info_file_handler': {'filename': '%s otc_tool.log' % strftime("%Y-%m-%d")}}}
                      )
    parser = argparse.ArgumentParser(description="This is an OTC tool for working with Jira projects.")
    connection_group=parser.add_argument_group(title="Connection control", description="About the connectionn to the server")
    connection_group.add_argument("-n", "--name", nargs='?', help="Alias for the target host" )
    connection_group.add_argument("-u", "--user", nargs='?', help="User Name (future)" )
    connection_group.add_argument("-p", "--password", nargs='?', help="Password (future)" )
    connection_group.add_argument("--scenario", nargs='?', help="Scenario to select", default='default')
    connection_group.add_argument("--query_set", nargs='?', help="Alternate query group name", default=None)
    project_group=parser.add_argument_group(title="Project control", description="Selecting which projects...")
    project_group.add_argument("--sproject", nargs='?', help="Jira source project")
    project_group.add_argument("--splatform", nargs='?', help="Jira source platform")
    project_group.add_argument("--sversion", nargs='?', help="Jira source android version")
    project_group.add_argument("--tplatform", nargs='?', help="Jira source platform")
    project_group.add_argument("--taversion", nargs='?', help="Android target version")
    project_group.add_argument("--tversion", nargs='?', help="Jira target android version")
    project_group.add_argument("--exists_on", nargs='?', help="Single value for Exists On field")
    project_group.add_argument("--update", default=None, action="store_true", help="Update target")
    project_group.add_argument("--rename", default=None, action="store_true", help="Rename source to target, if target is not found")
    project_group.add_argument("--verify", default=None, action="store_true", help="Verify target")
    parser.add_argument("--createmax", nargs='?', help="Max number of E-Features to create.",type=int)
    parser.add_argument("-c","--comment", nargs='?', help="Comment for created items.")
    parser.add_argument("-i","--input", nargs='?', help="Where to get the input.")
    parser.add_argument("-o","--output", nargs='?', help="Where to store the result.")
    parser.add_argument("-l", "--log_level", choices=['debug', 'info', 'warn', 'error', 'fatal'])
    parser.add_argument("command", choices=['help', 'compare_priorities', 'dump_parents', 'e_feature_scanner',
                                            'scan_areq_for_preq',
                                            'add_label_to_platform_version',
                                            'copy_platform_to_platform',
                                            'find_added_dng_vs_jira',
                                            'areq_superceded_by_preq',
                                            'label_from_labeled_items',
                                            'project_to_csv',
                                            ], default=None)
    args = parser.parse_args()

    # todo: Should be combined switches...
    if args.log_level is not None:
        log.logger.setLevel( log.logging.getLevelName(args.log_level.upper()))

    args.command = args.command.lower()

    try:
        scenario = get_server_info(args.scenario, SCENARIO_FILE)    # possible FileNotFoundError
        if scenario is None:
            raise NameError("Can't locate scenario {scenario} in scenario file.".format_map(vars(args)))
        for switch in vars(args):
            # -- If the switch is set, it should override whatever in in scenario...
            value = getattr(args, switch, None)
            if value is not None:
                scenario[switch] = value
        # -- todo: *this* would be the place to set defaults...


    except FileNotFoundError as f:
        log.logger.fatal("Can't open scenarios file: %s"%f)
        exit(-1)
    except NameError as f:
        log.logger.fatal("Error in scenarios file: %s"%f)
        exit(-1)

    if 'log_level' in scenario:
        log.logger.setLevel(log.logging.getLevelName(scenario['log_level'].upper()))

    log.logger.info("Combined Switches: %s", scenario)

    try:
        config = get_server_info(scenario['name'], CONFIG_FILE)    # possible FileNotFoundError
    except FileNotFoundError as f:
        log.logger.fatal("Can't open configuration file: %s"%f)
        exit(-1)

    queries = ''
    try:
        queries = get_server_info(scenario['name'], QUERIES_FILE)   # possible FileNotFoundError
    except FileNotFoundError as f:
        log.logger.fatal("Can't open queries file: %s", f)
        exit(-1)

    errors = 0
    if config is None:
        errors = 1
        log.logger.fatal("Configuration section for server %s is missing." % (args.name))
        exit(-1)
    if 'username' not in config:
        errors += 1
        log.logger.fatal("username for server %s is missing." % (args.name))
    if 'password' not in config:
        errors += 1
        log.logger.fatal("password for server %s is missing." % (args.name))
    if 'host' not in config:
        errors += 1
        log.logger.fatal("host url for server %s is missing." % (args.name))
    if errors > 0:
        log.logger.fatal("configuration errors were found, exiting." )
        exit(-1)

    # --> Dispatch to action routine:
    command = scenario['command']
    log.logger.info("Application Starting! Comamnd='%s'" % command)

    if 'help' == command:
        parser.print_help()
    elif 'compare_priorities' == command:
        compare_priorities(parser, scenario, config, queries)
    elif 'dump_parents' == command:
        dump_parents(parser, scenario, config, queries)
    elif 'e_feature_scanner' == command:
        e_feature_scanner(parser, scenario, config, CONFIG_FILE, queries)
    elif 'scan_areq_for_preq' == command:
        scan_areq_and_check_for_preq(parser, scenario, config, queries)
    elif 'copy_platform_to_platform' == command:
        copy_platform_to_platform(parser, scenario, config, queries, CONFIG_FILE, log=log)
    elif 'add_label_to_platform_version' == command:
        add_label_to_platform_version(parser, scenario, config, queries, CONFIG_FILE, log=log)
    elif 'find_added_dng_vs_jira' == command:
        find_added_dng_vs_jira(parser, scenario, config, queries, CONFIG_FILE, log=log)
    elif 'areq_superceded_by_preq' == command:
        areq_superceded_by_preq(parser, scenario, config, queries, CONFIG_FILE, log=log)
    elif 'label_from_labeled_items' == command:
        labeler = LabelFromLabeledItems(parser, scenario, config, queries, CONFIG_FILE, log=log)
        labeler.label_from_labeled_items()
    elif 'project_to_csv' == command:
        p2csv = ProjectToCSV(parser, scenario, config, queries, CONFIG_FILE, log=log)
        p2csv.run()
    else:
        parser.print_help()
        exit(1)

    log.logger.info( "Run completed." )
    return


if __name__ == "__main__":
    main()
    exit(0)


