#!/usr/bin/python
import os, sys
import shutil
import json
import operator
from optparse import OptionParser

SCRIPT_NAME = sys.argv[0]

## Supporting Functions
def fetch_env_var_val(env_var_name):
    '''
    '''
    if env_var_name in os.environ:
        return(os.environ[env_var_name])
    else:
        print(SCRIPT_NAME, ": Environment variable", env_var_name, "not found")
        return None

def get_intu_element_list(bootstrap_data_json, element_type_str, name_proto_str="Type_"):
    '''
    parses json structure from intu bootstrap.json config file and
    extracts list of element fields from top-level dict key matching "element_type_str"
    Inputs:
      bootstrap_data_json: json structure of bootstrap.json file (dict{list[dicts{}]})
      element_type_str: desired key of top-level json data to be parsed ex: "m_Agents"
      name_proto_str: 3rd-level key (varies by element type) to be returned as the "name"
        ex: name_proto_str="Type_" for agents; ="m_ServiceId" for serviceConfigs
    Returns: 
      list of element types (agent names, classifier names, serviceConfig Id's)
    '''
    if element_type_str in bootstrap_data_json:
       lst = bootstrap_data_json[element_type_str]
       return [lst[i][name_proto_str] for i in range(len(lst))]
    else:
       print("%s: Error: element % not in boostrap.json data" % (SCRIPT_NAME, element_type_str))
       return []

def set_intu_config_val(data, env_var):
    '''
    Read env_var input string, decompose, and find matching intu config parameter in json
      data dict
    Set intu config param to value pointed to by environment variable name
    See google spreadsheet doc for naming convention: 
      https://docs.google.com/spreadsheets/d/1J9RxQHpA0ZYXnvbDBzSFkyRsfA3vBhI9YRgxsxc0z6Q
    '''
    # Decompose environment variable name, get value
    tokens = env_var.split('_')[1:]   # first is prefix (not used)

    # Check for too-short/insufficient environment variable names
    if len(tokens) < 2:
       print("%s: warning: an apparent config environment variable was too short to be used: %s" 
        % (SCRIPT_NAME, env_var))
    
    # Check for intu member variables in last position
    if len(tokens[-2]) == 1:                            # yep: "m_User", etc
	tokens[-2] = '_'.join([tokens[-2], tokens[-1]]) # rebuild variable
        tokens.pop()

    # Parse out env var bits    
    name = tokens[0]         # ConversationV1, SpeechToTextV1, etc           (literal)
    param = tokens[1]        # m_User, m_Password, WorkspaceKey, WorkspaceId (literal)
        
    # Get env var value
    val = fetch_env_var_val(env_var)

    # Set the value in the json file
    err = set_config_val(data, name, param, val)

    return err


def set_config_val(data, name, param, value):
    '''
        # Set parameter values according to those passed in
        # Key on parameter:  USER, PASSWORD, URL, WorkspaceKey, WorkspaceID
        # 1) For USER: set m_User in an m_ServiceConfig
        # 2) For PASSWORD: set m_Password in an m_ServiceConfig
        # 3) For URL: set m_URL in an m_ServiceConfig
        # 3) For WKSPKEY: set m_WorkSpaceKey in an m_Classifier
        # 4) For WKSPID: set m_WorkSpaceID in an m_Classifier

        ex:
        m_ServiceConfigs: data["m_ServiceConfigs"][match "m_ServiceId"]{m_ServiceId, m_Password, m_URL, m_User}
        m_Classifiers:    data[m_Classifiers][match "Type_" : "TextClassifier"]["m_ClassifierProxies"][match m_ServiceId, m_WorkSpaceKey]{m_ServiceId, m_WorkspaceId, m_WorkSpaceKey}

    '''

    def set_ServiceConfigVal(data, param, name, value):
        ''' 
          Sets a value of a parameter in the definition of a ServiceConfig in Intu bootstrap.json
          Valid params: USER, PASSWORD, URL
          Valid names: Any m_ServiceId found in bootstrap.json template (i.e. ConversationV1)
          Valid values: Any value (not verified...)
        '''

        if param == "URL": 
	    param = "m_" + param
	else:
	    param = "m_" + param.title()
        matches = [pair for pair in enumerate(data["m_ServiceConfigs"]) if pair[1]["m_ServiceId"] == name]
        if len(matches) > 0:
            idx = matches[0][0]
            data["m_ServiceConfigs"][idx][param] = value     # Sets the value of m_User or m_Password
            print("%s: Set %s, %s %s:%s" % (SCRIPT_NAME, "m_ServiceConfigs", name, param, value))
            return 0
        else:
            print("%s: error, could not find ServiceId '%s' in 'm_ServiceConfigs' in json file" 
                % (SCRIPT_NAME, name))
        return 1

    def set_ClassifierProxyVal(data, param, name, value):
        ''' 
          Sets a value of a parameter in the definition of a ClassifierProxy in Intu bootstrap.json
          Valid params: WKSPKEY  ("WorkspaceKey" in bootstrap.json)
          Valid names: Any m_ServiceId found in bootstrap.json template (i.e. ConversationV1)
          Valid values: Any value (not verified...)
        '''        
        param = "m_WorkspaceId"
        matches = [pair for pair in enumerate(data["m_Classifiers"]) if "m_ClassifierProxies" in pair[1]]
        for pair in matches:
            idx = pair[0]
            cp = data["m_Classifiers"][idx]["m_ClassifierProxies"]
            for m in enumerate(cp):
                subidx = m[0]
                if cp[subidx]["m_ServiceId"] == name and cp[subidx]["m_WorkspaceKey"] == "self_dialog":
                    data["m_Classifiers"][idx]["m_ClassifierProxies"][subidx][param] = value
                    print("%s: Set %s, %s %s:%s" % (SCRIPT_NAME, "m_Classifiers", name, param, value))
                    return 0   # Success: parameter set

        # If not found:
        print("%s: error, could not find %s='self_dialog' in 'm_ClassifierProxies' with \
            ServiceId '%s' in json file" % (SCRIPT_NAME, "m_WorkspaceKey", name))
        return 1


    # Set the appropriate param / value in the json structure
    err = 0
    if param.upper() in ["USER", "PASSWORD", "URL"]:
        err = set_ServiceConfigVal(data, param.upper(), name, value)
        
    elif param.upper() == "WKSPID":
        err = set_ClassifierProxyVal(data, param.upper(), name, value)
        
    else: 
        print("%s: error, could not set %s:%s in json file." % (SCRIPT_NAME, param, name))
    return err


## Main
def main(args):
    #print SCRIPT_NAME, ": Main()"

    # # Check for and read Intu bootstrap file:
    # bootstrap_file = fetch_env_var_val("INTU_BOOTSTRAP_FILE_PATH")
    # if bootstrap_file == None:
    #     raise Exception("%s: Error: environment var not found." % SCRIPT_NAME)

    # Obtain bootstrap.json file path from input args
    bootstrap_file = ""
    parser = OptionParser(usage="usage: %prog [optional -f=filename]",
                          version="%prog 1.0")
    parser.add_option("-f", "--file",
                      action="store", # optional because action defaults to "store"
                      dest="bootstrap_file",
                      default="bootstrap.json",
                      help="bootstrap.json file to modify",)
    (options, args) = parser.parse_args()

    if len(args) > 1:
        parser.error("wrong number of arguments")
    bootstrap_file = options.bootstrap_file

    # Make a backup copy of the bootstrap.json file
    shutil.copy2(bootstrap_file, bootstrap_file+".bak")

    # Get environment variables having our prefix
    env_vars = []
    for env in os.environ:
        if env.startswith("WATSON"): 
            env_vars.append(env)
    
    # Read json bootstrap file, with intu config settings
    data = None
    with open(bootstrap_file, 'r') as infile:
        data = json.load(infile)

    # Set each environment variable value in our json structure ('data' passed by ref)
    for env in env_vars:
        err = set_intu_config_val(data, env)

    # Write out new bootstrap.json file
    with open(bootstrap_file, 'w') as outfile:
         json.dump(data, outfile, indent=4, sort_keys=True)

    sys.exit(0)

if __name__ == '__main__':
    main(sys.argv)
