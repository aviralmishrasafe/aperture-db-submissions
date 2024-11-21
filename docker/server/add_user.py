#add_user.py - temporary shim while not in adb

from aperturedb import Utils
import argparse

def get_args():
    class RoleGroupInfo:
        def __init__(self,c,r,u,d):
            self.c=c
            self.r=r
            self.u=u
            self.d=d
        @classmethod
        def All(cls):
            return RoleGroupInfo(True,True,True,True)
        @classmethod
        def JustRead(cls):
            return RoleGroupInfo(False,True,False,False)
        @classmethod
        def Nothing(cls):
            return RoleGroupInfo(False,False,False,False)

        def __repr__(self):
            #return f"create: {self.c} read: {self.r} update: {self.u} delete: {self.d}"
            return f"{self.c} {self.r} {self.u} {self.d}"
        def as_dict(self):
            return {
                    "create":self.c,
                    "read":self.r,
                    "update":self.u,
                    "delete":self.d
                    }
    class RoleInfo:
        def __init__(self,objects,indexes=RoleGroupInfo.JustRead(),
                access_control=RoleGroupInfo.Nothing()):
            self.objects=objects
            self.indexes=indexes
            self.access_control=access_control
        @classmethod
        def parsed(cls,data):
            groups=[]
            VALID_TRUE = ['t','true']
            VALID_FALSE =['f','false']
            valid = VALID_TRUE + VALID_FALSE
            split = data.split(':')
            if len(split) % 4 != 0:
                raise argparse.ArgumentException('groups of 4 needed for role info')
            for i in range(0,len(split),4):
                v=[]
                for j in range(i,i+4):
                    if split[j].lower() in VALID_TRUE:
                        v.append(True)
                    elif split[j].lower() in VALID_FALSE:
                        v.append(False)
                    else:
                        raise argparse.ArgumentException(f"{split[j]} isn't a valid value")

                groups.append(RoleGroupInfo(*v))
            return RoleInfo(*groups)

        def __repr__(self):
            return f"objects: ({self.objects}) indexes: ({self.indexes}) access_control: ({self.access_control})"


    parser = argparse.ArgumentParser()
    parser.add_argument('-u','--username')
    parser.add_argument('-p','--password')
    parser.add_argument('-e','--email', default="")
    parser.add_argument('-r','--role',action="append",default=[])
    parser.add_argument('-D','--default_role',default="user")
    parser.add_argument('--create_roles',action="store_true")
    parser.add_argument('--default_role_values', type=RoleInfo.parsed,default=RoleInfo(RoleGroupInfo.All(),indexes=RoleGroupInfo.All()))
    parser.add_argument('--construct_email', action="store_true")

    args = parser.parse_args()
    if args.email == "":
        if not args.construct_email:
            raise argparse.ArgumentTypeError("Need email or --construct_email")
        else:
            args.email = f"{args.username}@localhost"

    if len(args.role) == 0:
        args.role = [ args.default_role ]

    return args


def add_user(db,username,password,roles,email, opts):
    role_check_query=[{"GetRoles" : {
                    "roles":  roles 
                    }}]

    print(role_check_query)
    r,_ = db.query(role_check_query)
    existing_roles = [ k for k in r[0]["GetRoles"].keys() if k not in ['status'] ]
    print(existing_roles)
    missing_roles = [ k for k in roles if k not in existing_roles ]

    role_add_query=[{"CreateRole": {
                    "name": None,
                    "objects": None,
                    "indexes": None,
                    "access_control":None
                    }
                    }]
    user_check_query=[{"GetUsers": {
                        "users": [ username ]
                    }
                    }]
    create_query=[{"CreateUser": {
                "username": username,
                "password": password,
                "roles" : roles,
                "email": email
                }
                }]

    #missing_roles=roles
    if len(missing_roles) !=0 and not opts.create_roles:
        raise Exception("Roles are missing, but instructed not to create roles.")
    for m in missing_roles:
        defaults= opts.default_role_values
        create_role = role_add_query[0]["CreateRole"]
        create_role["name"] = m
        create_role["objects"] = defaults.objects.as_dict()
        create_role["indexes"] = defaults.indexes.as_dict()
        create_role["access_control"] = defaults.access_control.as_dict()
        print(role_add_query)
        r,_ = db.query(role_add_query)
        print(r)

    print(user_check_query)
    r,_ = db.query(user_check_query)
    print(r)

    if username not in r[0]['GetUsers']:
        print(create_query)
        r,_ = db.query(create_query)
        print(r)

if __name__ == "__main__":
    opts = get_args()
    db = Utils.create_connector()
    add_user(db,opts.username,opts.password,opts.role,opts.email,opts)

