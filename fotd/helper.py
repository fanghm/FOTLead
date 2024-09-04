# helper functions

"""
Deduce a feature's release based on its priority
Known priority range for some releases:
24R2: 32000-32999 (I1, I1.1, I1.2, P2)
24R3: 34000-34999 (I1, I1.1, I1.2, P2)
25R1: 36000-36999 (I1, I1.1, I1.2, P2)
25R2: 38000-38999 (I1 50%, I1, I1.1, I1.2, P2)
25R3: 40000-40999 (I1 50%, I1, I1.1, I1.2, P2)
26R1: 42000-42999 (I1 50%, I1, I1.1, I1.2, P2)
"""
def calc_release_per_priority(priority):
    # take 24R2 as the start point
    start_year = 24
    start_rel = 2
    start_priority = 32000

    range_span = 2000
    rel_number_per_year = 3

    if (priority < start_priority):
        print(f"Priority before 24R2 (<{start_priority}) not supported: {priority}")
        return None

    if (priority - start_priority) % range_span >= 1000:
        print(f"Invalid priority: {priority}, pls contact the Admin.")
        return None

    release_incr = (priority - start_priority) // range_span
    year_incr = (start_rel + release_incr - 1) // rel_number_per_year

    year = start_year + year_incr
    release = start_rel + release_incr - year_incr * 3

    # print(f"priority: {priority} \nrelease_incr: {release_incr} \nyear: {year}, release: {release} \n{year}R{release}")
    return f"{year}R{release}"

FEATURE_TYPES = [
		('Regular', 'Regular'),
		('eLLF_incoming', 'eLLF incoming'),
		('LLF_incoming', 'LLF incoming'),
		('Outgoing_LLF', 'Outgoing LLF'),
		('Outgoing_eLLF', 'Outgoing eLLF'),
	]
"""
Calculate the feature boundary category based on the feature's priority and csr_list
---
1, 如果feature的priority是24R3的，同时它的PSR=25R1，那它对于25R1而言就是属于LLF incoming；
2, 如果feature的priority是24R2及其之前的，同时其PSR=25R1，则它对于25R1而言就是eLLF incoming； 
3, 当feature是25R1的priority，且PSR=25R2，则对于25R1而言它就是outgoing LLF；
4, 当feature是25R1的priority，且PSR=25R3或更晚的release，则对于25R1而言它就是outgoing eLLF
so, 如果feature是25R1的priority，且PSR=25R2， 那么它在25R1 program 来看，属于outgoing LLF；但对于25R2 program来看就属于LLF incoming 

Parameters:
priority (int): feature's priority
csr_list (list): Contributing System Releases that are unique, continous, and sorted from the earliest to the latest.

Returns:
list: feature boundary category, could be one or two groups of results
"""
def get_feature_boundary_category(priority, csr_list):
    starting_release = calc_release_per_priority(priority)
    if starting_release is None or not csr_list or csr_list[0] != starting_release:
        return None

    csr_list_size = len(csr_list)
    # print(f"csr_list_size: {csr_list_size}")
    # psr = csr_list[-1]

    # use a map to map csr_list_size to the corresponding return value
    boundary_mapping = {
        1: [(starting_release, 'Regular')],
        2: [(starting_release, 'Outgoing LLF'), (csr_list[-1], 'LLF incoming')],
        3: [(starting_release, 'Outgoing eLLF'), (csr_list[-1], 'eLLF incoming')]
    }

    return boundary_mapping.get(csr_list_size, None)