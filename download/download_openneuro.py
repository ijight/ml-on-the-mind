import requests
import json
import os

def fetch_all_datasets(modality=None, output_json='data/openneuro_datasets.json'):
    url = "https://openneuro.org/crn/graphql"
    datasets = []
    has_next_page = True
    after_cursor = None

    if os.path.exists(output_json):
        with open(output_json, 'r') as f:
            existing_datasets = json.load(f)
            existing_ids = {d['metadata']['datasetId'] for d in existing_datasets}
            datasets.extend(existing_datasets)
    else:
        existing_ids = set()

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
        variables = {
            "first": 1000,
            "after": after_cursor,
            "modality": modality
        }

        response = requests.post(
            url,
            json={'query': query, 'variables': variables}
        )

        if response.status_code != 200:
            raise Exception(f"Query failed with status code: {response.status_code}")

        result = response.json()

        if 'data' in result and 'datasets' in result['data']:
            current_datasets = result['data']['datasets']['edges']
            new_datasets = []
            
            for edge in current_datasets:
                dataset = edge['node']
                dataset_id = dataset['metadata']['datasetId']
                if dataset_id not in existing_ids:
                    new_datasets.append(dataset)
                    existing_ids.add(dataset_id)
            
            if new_datasets:
                datasets.extend(new_datasets)
                
                with open(output_json, 'w') as f:
                    json.dump(datasets, f, indent=2)
                
                print(f"Fetched {len(current_datasets)} datasets, {len(new_datasets)} new. Total unique: {len(existing_ids)}")
            else:
                print(f"Fetched {len(current_datasets)} datasets, all duplicates. Total unique: {len(existing_ids)}")
            
            page_info = result['data']['datasets']['pageInfo']
            has_next_page = page_info['hasNextPage']
            after_cursor = page_info['endCursor']
        else:
            print("No data received in response")
            break

    return datasets

if __name__ == "__main__":
    all_datasets = fetch_all_datasets()
    print(f"\nTotal unique datasets fetched: {len(all_datasets)}")
    
    print("\nSample of datasets:")
    for dataset in all_datasets[:5]:
        print(f"- {dataset['name']}: {dataset['metadata']['datasetName']}")