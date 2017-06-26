from starflow.linkmanagement import LinksFromOpsWithTimes
import json

def sort_LL(FileList):
    """ gets LL with times executed field
    adjusts the LinkType values so they can be sorted
    sorts the LL based on both fields
    """
    LL_with_times = LinksFromOpsWithTimes(FileList)

    i=0
    while LL_with_times['LinkType'][i]=="CreatedBy":
        LL_with_times['LinkType'][i] = "xCreatedBy"
        i+=1

    LL_with_times.sort(order=['time_executed', 'LinkType'])

    return LL_with_times

def get_defaults(FileList):
    """ sets the default requirement fields for the Prov-JSON FileList
    adds an environment node and a start node
    """
    result = {}
    activity_d = {}
    environment_d = {}

    environment_d['rdt:language'] = "R"
    environment_d["rdt:script"] = FileList[0]
    activity_d['environment'] = environment_d

    start_node_d = {}

    start_node_d['rdt:name'] = FileList[0]
    start_node_d['rdt:type'] = "Start"
    start_node_d["rdt:elapsedTime"] = "0.5"
    keys = ["rdt:scriptNum", "rdt:startLine", "rdt:startCol", "rdt:endLine", "rdt:endCol"]
    for key in keys:
        start_node_d[key] = "NA"

    activity_d['p1'] = start_node_d
    result['activity']= activity_d

    keys = ["entity", "wasInformedBy", "wasGeneratedBy", "used"]
    for i in range (0, len(keys)):
        result[keys[i]]={}

    return result

def add_function(LinkType, result, links_to_p_count, p_count):
    """ if the process has not been added the dictionary
    adds it to the main dictionary to be pickled
    and the other dictionary that maps functions to numbers p1, p2, p3...
    returns this node number as a string
    and the current p_count for the next node
    """
    current_process_node = {}

    name_array = LinkType.split(".")
    name_pieces = name_array[-2:]
    name_string = ".".join(name_pieces)

    current_process_node['rdt:name'] = name_string
    current_process_node['rdt:type'] = "Operation"
    current_process_node["rdt:elapsedTime"] = "0.5"
    keys = ["rdt:scriptNum", "rdt:startLine", "rdt:startCol", "rdt:endLine", "rdt:endCol"]

    for key in keys:
        current_process_node[key] = "NA"

    pkey_string = "p" + str(p_count)
    p_count+=1

    links_to_p_count[LinkType] = pkey_string
    result["activity"][pkey_string] = current_process_node

    return pkey_string, p_count, links_to_p_count

def add_data(LinkType, result, links_to_d_count, d_count):
    """ if the data has not been added the dictionary
    adds it to the main dictionary to be pickled
    and the other dictionary that maps data nodes to numbers d1, d2, d3...
    returns this node number as a string
    and the current d_count for the next node
    """
    current_data_node = {}

    name_array = LinkType.split("/")
    name_string = name_array[-1]

    current_data_node['rdt:name'] = name_string
    current_data_node['rdt:value'] = LinkType
    current_data_node['rdt:type'] = "File"

    keys = ['rdt:scope', "rdt:fromEnv", "rdt:timestamp", "rdt:location"]
    values = ["undefined", "FALSE", "", ""]

    for i in range (0, len(keys)):
        current_data_node[keys[i]] = values[i]

    dkey_string = "d" + str(d_count)
    d_count+=1

    links_to_d_count[LinkType] = dkey_string
    result["entity"][dkey_string] = current_data_node

    return dkey_string, d_count, links_to_d_count

def add_depends_on_link(result, link, p_count, d_count, e_count, links_to_p_count, links_to_d_count, p_nodes_to_source_d_nodes, d_nodes_to_source_p_nodes):
    """ if the link is a depends_on link
    uses LinkTarget as the process node
    uses LinkSource as the data node
    makes a "used" edge
    """
    # add a process node if needed and return the process node number
    if link['LinkTarget'] not in links_to_p_count.keys():
        pkey_string, p_count, links_to_p_count = add_function(link['LinkTarget'], result, links_to_p_count, p_count)
    else:
        pkey_string = links_to_p_count[link['LinkTarget']]

    # add a data node if needed and return the data node number
    if link['LinkSource'] not in links_to_d_count.keys():
        # integers/non-File nodes?
        dkey_string, d_count, links_to_d_count = add_data(link['LinkSource'], result, links_to_d_count, d_count)
    else:
        dkey_string = links_to_d_count[link['LinkSource']]

    # use the node numbers to make a "used" edge
    e_string = "e" + str(e_count)

    current_used_node = {}
    current_used_node['prov:activity'] = pkey_string
    current_used_node['prov:entity'] = dkey_string

    e_count+=1

    result["used"][e_string] = current_used_node

    # store the information into another dictionary for creating "informs" edges
    if pkey_string not in p_nodes_to_source_d_nodes.keys():
        p_nodes_to_source_d_nodes[pkey_string] = []
    p_nodes_to_source_d_nodes[pkey_string].append(dkey_string)

    return p_count, d_count, e_count, links_to_p_count, links_to_d_count, p_nodes_to_source_d_nodes, d_nodes_to_source_p_nodes

def check_first_informer(result, link, e_count, first_time, links_to_p_count):
    """ uses the time executed field of the LL
    to connect the start node to the first process node
    to improve the layout of the DDG """

    # add a link from the start node to the process node depending on time_executed
    if link['time_executed'] == first_time:
        pkey_string = links_to_p_count[link['LinkTarget']]

        current_informer_node = {}
        current_informer_node['prov:informant'] = "p1"
        current_informer_node['prov:informed'] = pkey_string

        e_string = "e" + str(e_count)
        e_count+=1

        result['wasInformedBy'][e_string] = current_informer_node

    return e_count

def add_creates_link(result, link, p_count, d_count, e_count, links_to_p_count, links_to_d_count, p_nodes_to_source_d_nodes, d_nodes_to_source_p_nodes):
    """ if the link is a creates link
    uses LinkSource as the process node
    uses LinkTarget as the data node
    makes a "wasGeneratedBy" edge
    """
    # add a process node if needed and return the process node number
    if link['LinkSource'] not in links_to_p_count.keys():
        pkey_string, p_count, links_to_p_count = add_function(link['LinkSource'], result, links_to_p_count, p_count)
    else:
        pkey_string = links_to_p_count[link['LinkSource']]

    # add a data node if needed and return the data node number
    if link['LinkTarget'] not in links_to_d_count.keys():
        # integers/non-File nodes?
        dkey_string, d_count, links_to_d_count = add_data(link['LinkTarget'], result, links_to_d_count, d_count)
    else:
        dkey_string = links_to_d_count[link['LinkTarget']]

    # use the node numbers to make a "wasGeneratedBy" edge
    e_string = "e" + str(e_count)

    current_used_node = {}
    current_used_node['prov:activity'] = pkey_string
    current_used_node['prov:entity'] = dkey_string

    e_count+=1

    result["wasGeneratedBy"][e_string] = current_used_node

    # store the information into another dictionary for creating "informs" edges
    if dkey_string not in d_nodes_to_source_p_nodes.keys():
        d_nodes_to_source_p_nodes[dkey_string] = []
    d_nodes_to_source_p_nodes[dkey_string].append(pkey_string)

    # create an informs edge using the dictionaries
    try:
        temp = p_nodes_to_source_d_nodes[pkey_string]
        for i in temp:
            try:
                test = d_nodes_to_source_p_nodes[i]
                for j in test:
                    e_string = "e" + str(e_count)
                    e_count+=1

                    current_informer_node = {}
                    current_informer_node['prov:informant'] = j
                    current_informer_node['prov:informed'] = pkey_string

                    result['wasInformedBy'][e_string] = current_informer_node

            except:
                print("Key error in second step")
    except:
        print("key error in first step")

    return p_count, d_count, e_count, links_to_p_count, links_to_d_count, p_nodes_to_source_d_nodes, d_nodes_to_source_p_nodes

def make_dict(LL, FileList, first_time):
    """ writes the dictionary using information from the LL """

    # initialize the dictionary
    result = get_defaults(FileList)

    p_count = 2
    d_count = 1
    e_count = 1

    links_to_p_count = {}
    links_to_d_count = {}
    p_nodes_to_source_d_nodes = {}
    d_nodes_to_source_p_nodes = {}

    # iterate through each item in the LL and use the information to add to the dictionary
    for link in LL:
        if link['LinkType'] == "DependsOn":
            p_count, d_count, e_count, links_to_p_count, links_to_d_count,p_nodes_to_source_d_nodes, d_nodes_to_source_p_nodes = add_depends_on_link(result, link, p_count, d_count, e_count, links_to_p_count, links_to_d_count, p_nodes_to_source_d_nodes, d_nodes_to_source_p_nodes)
            e_count = check_first_informer(result, link, e_count, first_time, links_to_p_count)
        else: #LinkType == Creates
            p_count, d_count, e_count, links_to_p_count, links_to_d_count, p_nodes_to_source_d_nodes, d_nodes_to_source_p_nodes = add_creates_link(result, link, p_count, d_count, e_count, links_to_p_count, links_to_d_count, p_nodes_to_source_d_nodes, d_nodes_to_source_p_nodes)

    # add finish node? 

    return result

def write_json(dictionary, output_json_file):
    with open(output_json_file, 'w') as outfile:
        json.dump(dictionary, outfile)

def StarFlowLL_to_DDG(FileList, output_json_file):
    """ uses the StarFlow.LinkManagement operation LinksFromOpsWithTimes
    to obtain a LL
    Uses information from LL and time_executed to make a PROV_JSON file
    that can be read by DDGExplorer

    Input:
    FileList, a list of python modules for which links will be found
        the first module name will be used as the script name for the start node in the DDG
    output_json_file, a filepath where the PROV_JSON file will be written
        open this file using DDGExplorer "open from file" option """

    #get LL
    LL = sort_LL(FileList)
    # store the first time to make an informs node
    #from the start process node to the first process node
    first_time = LL[0]['time_executed']

    # write to prov-json format
    nested_dict = make_dict(LL, FileList, first_time)

    # write to file
    write_json(nested_dict, output_json_file)

def main():

    FileList = ['/Users/jen/Desktop/Env/scripts/my_module.py']
    output_json_file = "/Users/jen/Desktop/Env/json_tests/dictionary_module.json"

    StarFlowLL_to_DDG(FileList, output_json_file)

    # open using DDGExplorer "Open From File".

if __name__ == "__main__":
    main()
