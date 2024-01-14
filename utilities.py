def flatten_list_of_lists(list_of_lists: list) -> list:
    return [item for sublist in list_of_lists for item in sublist]
