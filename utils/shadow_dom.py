DEEP_FIND_JS = """
function deepFindAll(root, selector, results = []) {
    if (!root) return results;
    results.push(...root.querySelectorAll(selector));
    for (const node of root.querySelectorAll('*')) {
        if (node.shadowRoot) {
            deepFindAll(node.shadowRoot, selector, results);
        }
    }
    return results;
}
"""
