The objects are:
User
Group
File

Users and Groups have links to files that describe ownership.
Groups consist of users and Groups.

Users are linked to Groups by 'GroupMember' connections
and Groups are linked to groups by 'InnerGroup' connections

We will make 'SimpleGroup' which are constructed, and flatten any group with
other member groups into just their users. SimpleGroups are then linked to the
Group they are the decomposed version of.

This allows us to do a query for permissions on a file by doing

{ FindEntity type: user, constraint{ user_id} , ref 1 }
{ FindEntity type: simplegroup , connected_to {  ref 1 } , ref 2 }
{ FindEntity type: group , connected_to {  ref 2 } , ref 3 }
{ FindEntity type: file, connected_to{ 1 or 3 }}

We are calling the link between SimpleGroup and User 'ReducedUser' since it
doesn't represent actual membership in a group, but an effective membership.

The link between SimpleGroup and Group is 'GeneratedGroup'
