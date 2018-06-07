# simple module to wrap jira customfield lookups
# testing this was probably overkill

import unittest

_field_lookup = None
def make_field_lookup(jira):
    global _field_lookup
    if _field_lookup is None:
        fields = jira.fields()
        fl = JiraFieldLookup(fields)
        _field_lookup = fl

    return _field_lookup


class JiraFieldLookup(object):
    def __init__(self, fields):
        self._lookup = {}
        self._reverse = {}

        for field in fields:
            i = field['id']
            n = field['name']
            self._lookup[i] = n
            self._reverse[n] = i

    def __getitem__(self, key):
        return self._lookup[key]

    def reverse(self, key):
        return self._reverse[key]


class TestJiraFieldLookup(unittest.TestCase):
    def setUp(self):
        self.testfields = [
            {u'clauseNames': [u'cf[19200]', u'Rejected Reason'],
              u'custom': True,
              u'id': u'customfield_19200',
              u'name': u'Rejected Reason',
              u'navigable': True,
              u'orderable': True,
              u'schema': {u'custom': u'com.atlassian.jira.plugin.system.customfieldtypes:select',
                          u'customId': 19200,
                          u'type': u'string'},
              u'searchable': True},
             {u'clauseNames': [u'cf[19202]', u'Revision'],
              u'custom': True,
              u'id': u'customfield_19202',
              u'name': u'Revision',
              u'navigable': True,
              u'orderable': True,
              u'schema': {u'custom': u'com.atlassian.jira.plugin.system.customfieldtypes:textfield',
                          u'customId': 19202,
                          u'type': u'string'},
              u'searchable': True},
             {u'clauseNames': [u'resolution'],
              u'custom': False,
              u'id': u'resolution',
              u'name': u'Resolution',
              u'navigable': True,
              u'orderable': True,
              u'schema': {u'system': u'resolution', u'type': u'resolution'},
              u'searchable': True}
        ]

    def test_single(self):
        f = self.testfields[0]
        fl = JiraFieldLookup([f])
        self.assertEqual(fl['customfield_19200'], 'Rejected Reason')
        self.assertEqual(fl.reverse('Rejected Reason'), 'customfield_19200')

    def test_multi(self):
        f = self.testfields
        fl = JiraFieldLookup(f)
        self.assertEqual(fl['customfield_19200'], 'Rejected Reason')
        self.assertEqual(fl['customfield_19202'], 'Revision')
        self.assertEqual(fl['resolution'], 'Resolution')

        self.assertEqual(fl.reverse('Rejected Reason'), 'customfield_19200')
        self.assertEqual(fl.reverse('Revision'), 'customfield_19202')
        self.assertEqual(fl.reverse('Resolution'), 'resolution')


if __name__ == '__main__':
    unittest.main()

"""
[{u'clauseNames': [u'cf[19200]', u'Rejected Reason'],
  u'custom': True,
  u'id': u'customfield_19200',
  u'name': u'Rejected Reason',
  u'navigable': True,
  u'orderable': True,
  u'schema': {u'custom': u'com.atlassian.jira.plugin.system.customfieldtypes:select',
              u'customId': 19200,
              u'type': u'string'},
  u'searchable': True},
 {u'clauseNames': [u'cf[19202]', u'Revision'],
  u'custom': True,
  u'id': u'customfield_19202',
  u'name': u'Revision',
  u'navigable': True,
  u'orderable': True,
  u'schema': {u'custom': u'com.atlassian.jira.plugin.system.customfieldtypes:textfield',
              u'customId': 19202,
              u'type': u'string'},
  u'searchable': True},
 {u'clauseNames': [u'cf[12011]', u'Related Customer Bug'],
  u'custom': True,
  u'id': u'customfield_12011',
  u'name': u'Related Customer Bug',
  u'navigable': True,
  u'orderable': True,
  u'schema': {u'custom': u'com.atlassian.jira.plugin.system.customfieldtypes:labels',
              u'customId': 12011,
              u'items': u'string',
              u'type': u'array'},
  u'searchable': True},
 {u'clauseNames': [u'cf[17700]', u'Value Added'],
  u'custom': True,
  u'id': u'customfield_17700',
  u'name': u'Value Added',
  u'navigable': True,
  u'orderable': True,
  u'schema': {u'custom': u'com.atlassian.jira.plugin.system.customfieldtypes:select',
              u'customId': 17700,
              u'type': u'string'},
  u'searchable': True},
 {u'clauseNames': [u'resolution'],
  u'custom': False,
  u'id': u'resolution',
  u'name': u'Resolution',
  u'navigable': True,
  u'orderable': True,
  u'schema': {u'system': u'resolution', u'type': u'resolution'},
  u'searchable': True}]
"""
