#!/usr/bin/env python

from gojira import init_jira, jql_issue_gen, issue_keys_issue_gen
from jirafields import make_field_lookup

#PROJECT = 'AREQ'
#ISSUETYPE = 'E-Feature'
#ASSIGNEE = ''
#VAL_LEAD = 'wilcoxjx'
AND_VER = "O"
#PLATFORM = 'Broxton-P IVI"'
droid_ver_id = 'customfield_10811'

def create_from_jql(j):
    i = 0

    fl = make_field_lookup(j)
    and_vers_key = fl.reverse('Android Version(s)')
    platprog_key = fl.reverse('Platform/Program')

    #jql = """project = CREQ AND issuetype = Feature AND assignee = swmckeox"""
    jql = """project = %s AND issuetype = Feature"""%(PROJECT,)
    for areq in jql_issue_gen(jql, j):
        print areq.key, areq.fields.summary, getattr(areq.fields, and_vers_key)[0].value

        for platprog in getattr(areq.fields, platprog_key):
            # Create Sub-task
            i += 1
            and_ver = getattr(areq.fields, and_vers_key)[0].value

            ### Nerfed for safety
            #print i, areq.key, platprog.value
            #efeature=create_e_feature_from_feature(j, areq, ASSIGNEE, VAL_LEAD, and_ver, platprog.value)
            #new_sum = efeature.fields.summary.replace('[]', '[4.4]')
            #efeature.update(fields={'summary':new_sum})
            #print "\t", efeature.key,efeature.fields.summary, getattr(efeature.fields, and_vers_key)[0].value
            #print "\t", efeature.key,efeature.fields.summary, getattr(efeature.fields, and_vers_key)[0].value

def add_value_to_list(issue, key, new_value):
    values = [x.value for x in getattr(issue.fields, key)]
    if new_value not in values:
        values.append(new_value)
        update = [{'value':v} for v in values]
        issue.update(fields = {key: update})


def ensure_parent_feature(jira, issue):
    if issue.fields.issuetype.name == 'E-Feature':
        feature_key = issue.fields.parent.key
        feature = j.issue(feature_key)
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
        print "-"*40
        print source_issue.key, source_issue.fields.summary

        feature = ensure_parent_feature(j, source_issue)

        print feature.key, feature.fields.summary

        add_value_to_list(feature, platprog_key, NEW_PLATFORM)
        efeature = create_e_feature_from_feature(jira, feature, ASSIGNEE, VAL_LEAD, AND_VER, NEW_PLATFORM)

        create_count += 1
        print efeature.key, efeature.fields.summary, getattr(efeature.fields, and_vers_key)

    print "created {} new e-features".format(create_count)


def add_dessert(j, jql, dessert):
    update_count = 0

    fl = make_field_lookup(j)
    and_vers_key = fl.reverse('Android Version(s)')


    for issue in jql_issue_gen(jql, j, count_change_ok=True):
        print issue.key
        add_value_to_list(issue, and_vers_key, 'O')
        update_count += 1

    print "Updated {} issues".format(update_count)

def clone_efeature_add_dessert(j, jql, dessert):
    update_count = 0
    fl = make_field_lookup(j)
    print "JQL: " + jql
    val_lead_key = fl.reverse('Validation Lead')
    and_vers_key = fl.reverse('Android Version(s)')
    platprog_key = fl.reverse('Platform/Program')

    for issue in jql_issue_gen(jql, j, count_change_ok=True):
        print issue.key
        print issue.fields.parent.key
        print issue.fields.summary
        parent_platform = getattr(issue.fields, 'customfield_13603')[0].value
        print parent_platform
        new_efeature_dict = {
                'project': {'key': issue.fields.project.key},
                'parent': {'key': issue.fields.parent.key},
                #'status': issue.fields.status.name,
                'summary': issue.fields.summary,
                'issuetype': {'name': 'E-Feature'},
                'assignee': {'name': issue.fields.assignee.name},
                and_vers_key: [{'value': 'O'}],
                platprog_key: [{'value': parent_platform}]
        }
        
        efeature = jira.create_issue(fields=new_efeature_dict) 
        update_count += 1

    print "Updated {} issues".format(update_count)

if __name__ == "__main__":
    jira = init_jira()
    jql = """project = AREQ AND issuetype = E-Feature AND status in ("In Progress") AND "Android Version(s)" in (N) AND "Platform/Program" in ("Broxton-P IVI") AND Source ~ IOTG-TSD"""
    clone_efeature_add_dessert(jira, jql, "O")
    #new_jql = """project = AREQ AND issuetype = E-Feature AND status in (Open, "In Progress", Closed, Merged) AND "Android Version(s)" in (N) AND "Platform/Program" in ("Broxton-P IVI")"""
    #old_jql = """project = AREQ and issuetype = Feature and "Android Version(s)" in (N, N-MR0, N-MR1, N-MR2) and "Android Version(s)" != O and  status not in (Rejected, Deprecated)"""
    #add_dessert(jira, jql, "O")
    #create_from_efeature_key_list(jira, 'creq_apollo_lake.txt')