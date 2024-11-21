import pandas as pd
import math
import sys
from aperturedb import Utils



def load_db(db,users,groups,simple_groups):
    for u in users:
        query = [{
            "AddEntity": {
                "class": "User",
                "properties": {
                    "name": u.user,
                    "system_id": int(u.system_id)
                }
            }
        }]
        print(query)
        db.query(query)
        if not db.last_query_ok():
            print("Error Add User")
            db.print_last_response()
            return


    for g in groups:
        query=[{
            "FindEntity": {
                    "with_class": "User",
                    "_ref":1,
                    "constraints": {
                        "system_id" : ["in",[ int(uid) for uid in g.user_ids]]
                    }
                }
            },{
            "AddEntity": {
                "class": "Group",
                "properties": {
                    "name": g.name,
                    "system_id": int(g.system_id)
                },
                "connect": {
                    "ref":1,
                    "class":"GroupMember"
                }
            }
        }]
        print(query)
        db.query(query)
        if not db.last_query_ok():
            print("Error Add Group")
            db.print_last_response()
            return


    # add group links in phase 2. ( easier than trying to sort out ordering )
    for g in groups:
        if len(g.group_ids) == 0:
            continue

        query=[{
            "FindEntity": {
                "with_class": "Group",
                "constraints": {
                    "system_id": ["==", int(g.system_id) ]
                    },
                "_ref":1
                }
            }, {
            "FindEntity": {
                "with_class":"Group",
                "constraints": {
                    "system_id": ["in", g.group_ids ]
                    },
                "_ref":2
                }
            }, {
                "AddConnection": {
                    "class":"InnerGroup",
                    "src":1,
                    "dst":2
                }
        }]
        print(query)
        db.query(query)
        if not db.last_query_ok():
            print("Error Add Group Link")
            db.print_last_response()
            return

    # Simple groups don't need to be  1-1 mapping with real groups.
    # if the member list of a group was too big, you could
    # chunk it into smaller groups.

    # If regenerating group memberships a lot, that might be less useful.
    for group_id in simple_groups.keys():
        query=[{
            "FindEntity": {
                "with_class":"User",
                "constraints": {
                    "system_id": ["in",simple_groups[group_id][1]]
                    },
                "_ref":1
            }
        },{
            "AddEntity": {
                "class" :"SimpleGroup",
                "properties": {
                    "generated_id":group_id
                },
                "connect": {
                    "ref":1,
                    "class": "ReducedUser",
                    "direction":"in"
                }
            }
        }]
        print(query)
        db.query(query)
        if not db.last_query_ok():
            print("Error Add SimpleGroup")
            db.print_last_response()
            return
        query=[{
            "FindEntity": {
                "with_class": "SimpleGroup",
                "constraints": {
                    "generated_id":[ "==", group_id]
                },
                "_ref":1
            }
        },{
            "FindEntity": {
                "with_class":"Group",
                "constraints": {
                    "system_id": ["==", group_id ]
                },
                "_ref":2,
            }
        },{
            "AddConnection": {
                "class":"GeneratedGroup",
                "src":1,
                "dst":2
            }
        }]
        print(query)
        db.query(query)
        if not db.last_query_ok():
            print("Error Add SimpleGroup Link")
            db.print_last_response()
            return

def generate_simple_groups(groups):

    # make simple groups.
    # we have all data here now, but in more complex, you would load
    # non-delta from the db.

    # what we want is a list of all users in each group.
    simple_users = {} # maps group id to  pair of 'complete?' and ids.
    simple_id = 1
    print("gsg")

    new_groups = list(groups)
    working = []
    cycle_check = 0
    while len(new_groups) > 0 or len(working) > 0:
        mark_cycle = False
        # if new_groups, process first.
        if len(new_groups ) > 0:
            cur = new_groups.pop()
        else:
            cur = working.pop()

        cur_id = int( cur.system_id )

        # simple group
        if len(cur.group_ids) == 0:
            simple_users[cur_id] = [ True, cur.user_ids ]
            print(f"Simple Group for {cur.system_id}")
            simple_id = simple_id + 1
            # if end of first look, start cycle check.
            if len(new_groups) == 0:
              mark_cycle = True
        else:
            if not cur_id in simple_users:
                # add as not complete.
                simple_users[cur_id] =  [ False, cur.user_ids ]
            sublist = [ int(gid) in simple_users and simple_users[int(gid)][0] for gid in cur.group_ids ]
            print(f"Sublist for {cur_id} is {sublist} : {cur.group_ids}")
            # if we have all groups in finished state, add those users and mark complete.
            if all( sublist ):
                all_u = [simple_users[cur_id][1]] + [simple_users[int(gid)][1] for gid in cur.group_ids ]
                simple_users[cur_id ] = [True ,list(set([int(u) for tup in all_u for u in tup]))]
                print(f"Finished Group for {cur.system_id}")

                # reset cycle check if we've processed all items once.
                if len(new_groups) == 0:
                    mark_cycle = True

            else:
                print(f"Incomplete Group for {cur.system_id}")
                working.insert(0,cur)

        if mark_cycle:
            cycle_check = len(working)
        elif len(new_groups) == 0:
            cycle_check = cycle_check - 1
            if cycle_check <= 0:
                raise Exception("Unresolable cycle detected in groups")

    print(simple_users)
    # now we have simple_users complete- maps group names to [ group_complete , [ user_1 , user_2 .. user_N ] ]
    return simple_users

def load_files_db(db,files):
    file_id = 1
    for f in files:
        file_id = file_id + 1
        print(f)
        query=[{
            "FindEntity": {
                "with_class":"User",
                "constraints": {
                    "system_id": [ "==",  int(f.user_perms)]
                },
                "_ref":1
            }
        },{
            "AddEntity": {
                "class":"File",
                "properties": {
                    "name": f.name,
                    "file_id" : file_id
                },
                "connect": {
                    "ref":1,
                    "class":"FileOwner"
                }
            }
        }]
        print(query)
        db.query(query)
        if not db.last_query_ok():
            print("Error Add File")
            db.print_last_response()
            return

        query = [{
            "FindEntity": {
                "with_class":"Group",
                "constraints": {
                    "system_id": ["==", int(f.group_perms)]
                },
                "_ref":1
            }
        },{
            "FindEntity": {
                "with_class":"File",
                "constraints": {
                    "file_id": ["==", file_id]
                },
                "_ref":2
            }
        },{
            "AddConnection": {
                "class":"FileGroup",
                "src":2,
                "dst":1
            }
        }]
        print(query)
        db.query(query)
        if not db.last_query_ok():
            print("Error Add File Group Link")
            db.print_last_response()
            return

        

def load_data():
    ucsv = pd.read_csv( "users.csv")
    gcsv_raw = pd.read_csv("group.csv")
    files_raw = pd.read_csv("files.csv")

    def make_lists( row ):
        row['user_ids'] = row['user_ids'].split(',')
        gv = row['group_ids']
        row['group_ids'] = [] if isinstance(gv,float) and math.isnan(gv) else gv.split(',')
        return row

    def drop_perms( row ):
        # we drop off permissions here for simpler test.
        row['user_perms'] = int(row['user_perms'].split('_')[1])
        row['group_perms'] = int(row['group_perms'].split('_')[1])
        return row

    gcsv = gcsv_raw.apply(make_lists,axis=1)
    files = files_raw.apply(drop_perms,axis=1)

    ur = ucsv.to_records()
    gr = gcsv.to_records()
    fr= files.to_records()
    return [ur,gr,fr]

users,groups,files = load_data()
simple_groups = generate_simple_groups(groups)
print(users)
db = Utils.create_connector()
load_db(db,users,groups,simple_groups)

load_files_db(db,files)
