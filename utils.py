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

