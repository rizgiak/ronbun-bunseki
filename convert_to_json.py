import csv  
import json  
  
csv_file_path = 'data/output_5_st.csv'  
json_file_path = 'data/output_5_st.json'  
  
node_indices = {}  # A dictionary to store the mapping of node names to indices  
data = {  
    "nodes": [],  
    "links": []  
}  
  
def get_node_index(node_name):  
    if node_name not in node_indices:  
        node_indices[node_name] = len(node_indices)  
        data["nodes"].append({"name": node_name, "size": 0})  # Add "size" key with value 0 to each node  
    return node_indices[node_name]  
  
with open(csv_file_path, 'r', encoding='utf-8') as csv_file:  
    csv_reader = csv.DictReader(csv_file)  
    unique_rows = set()  # A set to store unique rows  
    for row in csv_reader:  
        source_name = row['source']  
        target_name = row['target']  
        if (source_name, target_name) in unique_rows:  # Skip duplicated rows  
            continue  
        unique_rows.add((source_name, target_name))  
          
        source_index = get_node_index(source_name)  
        target_index = get_node_index(target_name)  
          
        data["links"].append({"source": source_index, "target": target_index})  
          
        # Increment the value of "size" for the target node  
        data["nodes"][target_index]["size"] += 1  
  
# Save the data as JSON  
with open(json_file_path, 'w') as json_file:  
    json.dump(data, json_file, indent=2)  
