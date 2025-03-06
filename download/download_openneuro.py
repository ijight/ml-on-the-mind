import requests
import json
import os

def fetch_all_datasets(modality=None, output_json='data/openneuro_datasets.json'):
    url = "https://openneuro.org/crn/graphql"
    datasets = []
    has_next_page = True
    after_cursor = None
    
    # Load existing datasets if any
    if os.path.exists(output_json):
        with open(output_json, 'r') as f:
            existing_datasets = json.load(f)
            existing_ids = {d['metadata']['datasetId'] for d in existing_datasets}
            datasets.extend(existing_datasets)
    else:
        existing_ids = set()

    # The GraphQL query
    query = """
        query($after: String, $first: Int = 100, $modality: String) {
            datasets(first: $first, after: $after, modality: $modality) {
                edges {
                    node {
                        metadata {
                            species
                            datasetId
                            datasetName
                            associatedPaperDOI
                            modalities
                            tasksCompleted
                            datasetUrl
                        }
                        name
                        draft {
                            readme
                            size
                            files {
                                filename
                                directory
                            }
                        }
                        publishDate
                    }
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
    """

    while has_next_page:
        # Prepare the variables for the query
        variables = {
            "first": 1000,
            "after": after_cursor,
            "modality": modality
        }

        # Make the request
        response = requests.post(
            url,
            json={'query': query, 'variables': variables}
        )

        if response.status_code != 200:
            raise Exception(f"Query failed with status code: {response.status_code}")

        result = response.json()

        # Extract the data
        if 'data' in result and 'datasets' in result['data']:
            current_datasets = result['data']['datasets']['edges']
            new_datasets = []
            
            # Filter out duplicates
            for edge in current_datasets:
                dataset = edge['node']
                dataset_id = dataset['metadata']['datasetId']
                if dataset_id not in existing_ids:
                    new_datasets.append(dataset)
                    existing_ids.add(dataset_id)
            
            if new_datasets:
                # Add new datasets to main list
                datasets.extend(new_datasets)
                
                # Save all datasets to JSON
                with open(output_json, 'w') as f:
                    json.dump(datasets, f, indent=2)
                
                print(f"Fetched {len(current_datasets)} datasets, {len(new_datasets)} new. Total unique: {len(existing_ids)}")
            else:
                print(f"Fetched {len(current_datasets)} datasets, all duplicates. Total unique: {len(existing_ids)}")
            
            # Update pagination info
            page_info = result['data']['datasets']['pageInfo']
            has_next_page = page_info['hasNextPage']
            after_cursor = page_info['endCursor']
        else:
            print("No data received in response")
            break

    return datasets

# Example usage
if __name__ == "__main__":
    # Fetch all datasets (no modality filter)
    all_datasets = fetch_all_datasets()
    print(f"\nTotal unique datasets fetched: {len(all_datasets)}")
    
    # Example: Print first few dataset names
    print("\nSample of datasets:")
    for dataset in all_datasets[:5]:
        print(f"- {dataset['name']}: {dataset['metadata']['datasetName']}")

    # Optional: Filter by modality
    # mri_datasets = fetch_all_datasets(modality="MRI")
    # print(f"\nTotal MRI datasets: {len(mri_datasets)}")