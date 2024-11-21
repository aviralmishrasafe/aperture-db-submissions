from aperturedb import Utils
import argparse


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o','--owner',default=None, help='Check if person is owner')
    parser.add_argument('-g','--group',default=None,help='Check if group is on file')
    parser.add_argument('-a','--access',default=None, help='Check if user can access (via group or owner)')
    parser.add_argument('files',nargs='+',help='Files to check')
    return parser.parse_args()

def check_files(opt,db):
   
    for f in opt.files:
        if opt.owner is not None:
            print(f"Checking owner: {opt.owner}")
            query=[{
                "FindEntity": {
                    "with_class":"User",
                    "constraints": {
                        "system_id": ["==", int(opt.owner)]
                    },
                    "_ref":1
                }
            },{
                "FindEntity": {
                    "with_class":"File",
                    "constraints": {
                        "name": ["==",f]
                    },
                    "is_connected_to": {
                        "ref":1
                    },
                    "results": {
                        "count":True
                    }
                }
            }]
            print(query)
            res,_ = db.query(query)
            if not db.last_query_ok():
                db.print_last_response()
                raise Exception("Owner query failed")
            else:
                ownership= "is" if res[1]["FindEntity"]["count"] !=0 else "is not"
                print(f"{opt.owner} {ownership} owner of {f}") 
        if opt.access is not None:
            print(f"Checking access: {opt.access}")
            query=[{
                "FindEntity": {
                    "with_class":"User",
                    "constraints": {
                        "system_id": ["==", int(opt.access)]
                    },
                    "_ref":1
                }
            },{
                "FindEntity": {
                    "with_class":"SimpleGroup",
                    "is_connected_to": {
                        "ref": 1
                    },
                    "_ref":2
                }
            },{
                "FindEntity": {
                    "with_class":"Group",
                    "is_connected_to": {
                        "ref": 2
                    },
                    "_ref":3
                }
            },{
                "FindEntity": {
                    "with_class":"File",
                    "constraints": {
                        "name": ["==",f]
                    },
                    "is_connected_to": {
                        "any": [{
                            "ref":1
                        }, {
                            "ref":3
                        }]
                    },
                    "results": {
                        "count":True
                    }
                }
            }]
            print(query)
            res,_ = db.query(query)
            if not db.last_query_ok():
                db.print_last_response()
                raise Exception("Owner query failed")
            else:
                can_access= "can" if res[3]["FindEntity"]["count"] !=0 else "cannot"
                print(f"{opt.access} {can_access} access {f}") 


if __name__ == '__main__':
    args = get_args()
    db = Utils.create_connector()
    check_files(args,db)
