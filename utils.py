#!/usr/bin/env python3
import pysftp, yaml, socket, glob

def display_err_in_file(filename, line, column, message, length=1, nlines=3): # pylint: disable=R0913
    """Mark the source code error location in file and return a string for display"""
    with open(filename, "r") as file:
        return _display_err(filename, line, column, message, length, nlines, file.read())
def _display_err(filename, line, column, message, length, nlines, content): # pylint: disable=R0913
    """Mark the source code error location in content and return a string for display"""
    lines = content.splitlines()
    start = max(0, line+1-nlines)
    res = [f"File {filename}, line {line+1}:{column+1}"]
    res.append(str('-' * (len(res[0]) + 7)))
    res += lines[start:line+1]
    res += [(' ' * column) + ("^" * length), message]
    return "\n".join(res)

def gen_new_links_list():
    new_links_list = []
    for fn in glob.glob("links_*.yml"):
        new_links = {}
        try:
            new_links = yaml.safe_load(open(fn))
            new_links_list.append(new_links)
        except yaml.YAMLError as err:
            print(f'ERROR: the file "{fn}" is not a valid YAML file - ignoring this file.')
            if hasattr(err, 'problem_mark'):
                mark = getattr(err, 'problem_mark')
                problem = getattr(err, 'problem')
                message = f"Could not read {fn}:"
                message += "\n" + display_err_in_file(fn, mark.line, mark.column, problem)
            elif hasattr(err, 'problem'):
                problem = getattr(err, 'problem')
                message = f"Could not read {fn}: {problem}"
            else:
                message = f"Could not read {fn}: YAML Error"
    
            suggestion = f"There is a syntax error in your - please fix it and try again."
            print(message)
            print(suggestion)
            continue
        except OSError as err:
            msg = "Please ensure the file exists and you have the required access privileges."
            print(msg)
            continue
        except:
            print(f'Unknown error while loading the file "{fn}".')
            continue
    return new_links_list

def get_links():
    links_list = gen_new_links_list()
    links = {}
    for link_list in links_list:
        for header in link_list.keys():
            if " - " in header:
                area = header.split(" - ")[0].capitalize()
                subarea = header.split(" - ")[1].capitalize()
            else:
                area = "Misc"
                subarea = header.capitalize()
            if area not in links.keys(): 
                links[area] = {}
            if subarea not in links[area].keys():
                links[area][subarea] = []
            list_of_dics = [ { ky: link_list[header][ky] } for ky in link_list[header].keys() ]
            links[area][subarea] += list_of_dics
    # Order lists-of-items by number of items, for more compact display in the browser
    ordered_links = {}
    for area in links.keys():
        subarea_num_items = {}
        for subarea in links[area].keys():
             subarea_num_items[subarea] = len(links[area][subarea])
        sorted_subareas = sorted(subarea_num_items.items(), key=lambda item: item[1])
        ordered_links[area] = {}
        for subarea_num in sorted_subareas:
            subarea = subarea_num[0]
            ordered_links[area][subarea] = links[area][subarea]
    return ordered_links
    
def download_and_upload_links_files():
    ###### init vars
    local_host_name = socket.gethostname()
    local_links_fn = "links_"+ local_host_name +".yml"
    params = yaml.safe_load(open("params.yml"))
    sftpHostname = params["sftpHostName"]
    Username = params["userName"]
    Password = params["password"]
    affiliated_hosts = params["affiliated_hosts"]
    ###### Connect
    sftp = pysftp.Connection(host=sftpHostname, username=Username, password=Password)
    print("    Connection successfully established.")
    # Switch to a remote directory
    sftp.cwd('/downloads/links')
    #Upload the local links file
    print(f'    Uploading local links file "{local_links_fn}"')
    sftp.put(local_links_fn)

    #Upload the affiliated hosts file(s)
    if len(affiliated_hosts):
        print(f'    Uploading affiliated-hosts links file(s) {affiliated_hosts}')
        for ah in affiliated_hosts:
            fn = "links_"+ ah +".yml"
            sftp.put(fn)

    # Download all the non-native links files
    directory_structure = sftp.listdir_attr()
    for attr in directory_structure:
        fn = attr.filename
        should_dl_file = True
        if not fn.startswith("links_") and fn.endswith(".yml"):
            should_dl_file = False
        if fn==local_links_fn:
            should_dl_file = False
        host = fn[len("links_"):-len(".yml")]
        if host in affiliated_hosts:
            should_dl_file = False
        if should_dl_file:
            print(f'    Downloading remote links file "{fn}"')
            sftp.get(fn)
    sftp.close()


