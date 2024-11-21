#add_users.sh - create users passed in by tab seperated string
T=$'\t'
# example of what it looks like:
#USERS="fred${T}cow${T}joe${T}dog${T}jane"

if [[ "${ADB_USERS}" == "" ]]; then
    echo "User information array was empty"
    exit 1
fi

IFS=$'\t' read -r -a user_info <<< "$ADB_USERS"

items=${#user_info[@]}

if (( items % 2 )); then
    echo "User information array separated into ${items}. We expect an even number."
    exit 1
fi

i=0

while (( i < ${#user_info[@]} )); do
  (( j = i + 1 ))
  python3 ./add_user.py -u "${user_info[$i]}" -p "${user_info[$j]}" --construct_email --create_roles
  (( i += 2 ))
done

