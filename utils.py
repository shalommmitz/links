#!/usr/bin/env python3
import pysftp, yaml, socket, glob


page_template = """
    <!-- ----------
    ---- **AREA** -----
    ----------- -->\n
    <section id="**area**">
      **articles** 
    </section>
"""
article_template = """
      <article>
        <h2>**subarea**</h2>
        <ol>
          **links**
        </ol>
      </article>
"""


def gen_html_page(pages):
    nav_items = ""
    pages_txt = ""
    for page_name in sorted(list(pages.keys())):  
        print(page_name)
        nav_items += '        <a href="#'+ page_name.lower() +'">'+ page_name.capitalize() +'</a>\n'
        pages_txt += pages[page_name]
    html_page = open("index_html.template").read()
    html_page = html_page.replace("**NAV ITEMS**", nav_items[:-1])
    html_page = html_page.replace("**PAGES**", pages_txt)
    return html_page
    
def get_pages(links_list):
    # data strcture: top level key: area. Next leve: subarea. Next level: description (value is url)
    data = {}
    
    for links in links_list:
        keys = sorted(list(links.keys()))
        for key in keys:
            match key.count(" - "):
                case 0:
                    area = "General"
                    subarea = key
                case 1:
                    area = key.split(" - ")[0].strip()
                    subarea = key.split(" - ")[1].strip()
                case _:
                    print("wrong number of dashes (surranded by spaces) - should be zero or one")
                    print("   Offending line is: '"+key+"'")
                    print("Aborting")
                    exit()    
            if not area in data.keys(): data[area] = {}
            if not subarea in data[area].keys(): data[area][subarea] = {}
            for k in links[key].keys(): 
                if k in data[area][subarea].keys():
                    print(f"ERROR: the key '{k}' in area '{key}' is not unique")
                    exit()
                data[area][subarea][k] = links[key][k]
    pages = {}
    for area in sorted(data.keys()):
        articles = ""
        for subarea in data[area].keys():
            links = ""
            for descr in data[area][subarea].keys():
                url = data[area][subarea][descr]
                links += f'            <li><a href="{url}">{descr}</a></li>\n'
            articles += article_template.replace("**subarea**", subarea).replace("**links**", links)
        page = page_template.replace("**AREA**", area.upper()).replace("**area**", area.lower())
        page = page.replace("**articles**", articles)
        pages[area] = page
    return pages
    
def gen_simple_html_page(new_links_list):
    links = { }
    for new_links in new_links_list:
        for item in new_links.keys():
            if item==item.upper():
                c_item = item
            else:
                c_item = item.capitalize()
            if c_item in links.keys():
               links[c_item].update(new_links[item])
            else:
               links[c_item] = new_links[item]

    page = '''<!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <title>Links</title>
    </head>
    <body>
    '''                          
    item_keys = list(links.keys())
    item_keys.sort(key=lambda y: y.lower())
    for i in item_keys:
        page += f'{i} '
        item = links[i]
        if type(item)!=type({}):
            print(f'ERROR: Part of the item "{i}" is not a directory - Aborting')
            exit()
        # print(type(item), item)
        
        for description in item.keys():
            link = item[description]
            page += f'<a href="{link}">{description}</a>&nbsp;\n'
        page += '<br>'
    page += '''
    </body>
    </html>
    '''
    return page

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


