#!/usr/bin/env python

import json
from jira.client import JIRA
from gojira import init_jira
import sys
import pyexcel as pe
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# jira = JIRA(config.options, config.basic_auth)


# (source, destination)
# areqs = [
# ('PREQ-22152','PREQ-23770')
# ]

# import .xlsx file where first worksheet
# areqs = pe.iget_records(file_name="vlookup.xlsx")



def get_valid_transition(issue, transition_name):
    """Find Valid Transition for Issue"""
    transitions = jira.transitions(issue)

    # Find Transition ID
    for t in transitions:
        print t['name']
        if (transition_name == t['name']):
            return t['id']
    return None


def update_status(source, destination):
    """Attempt to Update Status"""

    print "TRANSITIONS IDS"
    print  "REJECTED: " + get_valid_transition(destination, "To Rejected")

    # Check for same status
    if (source.fields.status.name == destination.fields.status.name):
        return

    # Check for valid transition
    transition_id = get_valid_transition(destination, source.fields.status.name)

    # Update Status
    if (transition_id):
        transition_issue(destination, transition_id)

def vlookup_data(map_file):
    for preq in map_file:
        # Print
        print("GID %s matches N-dessert %s and O-dessert %s" % (preq['Global ID'], preq['O-dessert'], preq['N-dessert']))
        continue
    return 0

    print areq[0] + " -> " + areq[1]
    source = jira.issue(areq[0])
    destination = jira.issue(areq[1])

    # Updated Fields
    updated_fields = {}

    # Components
    all_components = []
    for component in source.fields.components:
        all_components.append({"name": component.name})
    if all_components:
        updated_fields["components"] = all_components

    # Fix Version/s
    fix_versions = []
    for version in source.fields.fixVersions:
        fix_versions.append({"name": version.name})
    if fix_versions:
        updated_fields["fixVersions"] = fix_versions

    # Exists On
    exists_on = []
    if source.fields.customfield_18202:
        for target in source.fields.customfield_18202:
            exists_on.append({"value": target.value})
    if exists_on:
        updated_fields["customfield_18202"] = exists_on

    # Verified On
    verified_on = []
    if source.fields.customfield_15301:
        for target in source.fields.customfield_15301:
            verified_on.append({"value": target.value})
    if verified_on:
        updated_fields["customfield_15301"] = verified_on

    # Planned Release
    if source.fields.customfield_18400:
        updated_fields["customfield_18400"] = {"value": source.fields.customfield_18400.value}

    # Actual Release
    if source.fields.customfield_17803:
        updated_fields["customfield_17803"] = {"value": source.fields.customfield_17803.value}

    # Test Date/Time
    if source.fields.customfield_12121:
        updated_fields["customfield_12121"] = source.fields.customfield_12121

    # Assignee
    assignee = source.fields.assignee
    if assignee:
        updated_fields["assignee"] = {"name":assignee.name}

    # Validation Lead
    validation_lead = source.fields.customfield_19700
    if validation_lead:
        updated_fields["customfield_19700"] = {"name": validation_lead.name}

    # Labels
    if source.fields.labels:
        destination.update(fields={"labels": source.fields.labels})

    # Update
    if updated_fields:
        destination.update(fields=updated_fields)

    # Status
    #update_status(source, destination)

    # Link
    #jira.create_issue_link("Duplicate",source,destination)

    # Link and Comment
    jira.create_issue_link("Duplicate",source,destination,
        comment={"body": "Platform Requirements have been transitioned to iCDG JAMA instance.\n\r\n\rReplacing '%s' --> '%s'" % (source.key, destination.key)})

    # Reject Source
    jira.transition_issue(source, 51)


if __name__ == "__main__":
#   jira = init_jira()
#   import .xlsx file where first worksheet
    preqs = pe.iget_records(file_name="vlookup.xlsx")
    vlookup_data(preqs)
    print "Operation complete."
    
