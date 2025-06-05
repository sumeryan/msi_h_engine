class UpdateTreeData:
    def __init__(self, tree_data: dict, formulas: dict, formulas_results: dict):
        self.tree_data = tree_data
        self.formulas = formulas
        self.formulas_results = formulas_results


    def search_node_path(self, path: str, data: dict) -> dict:
        """
        Searches for a node in the tree data based on the given path.
        :param path: The path to search for.
        :param data: The tree data to search within.
        :return: The node if found, otherwise None.
        """

        for node in data:
            if 'path' in node and node.get('path') == path:
                return node
            if 'data' in node and node['data']:
                found_node = self.search_node_path(path, node['data'])
                if found_node:
                    return found_node

    def update_tree(self):

        # Formula node
        path_node = self.formulas.get('path')
        update_node = self.search_node_path(path_node, self.tree_data['data'])

        # Update the node with the formula results
        for formula_result in self.formulas_results:
            for node in update_node['data']:
                if formula_result['id'] == node['id']:
                    for path_result in formula_result['results']:
                        for field in node['fields']:
                            if field['path'] == path_result['path']:
                                field['value'] = path_result['result']

        return self.tree_data
