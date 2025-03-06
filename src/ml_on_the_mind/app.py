import streamlit as st
import marqo
from collections import defaultdict
import traceback
from data.data_schema import DatasetMetadata
from data.utils import load_datasets

def format_size(size_in_bytes):
    # Convert bytes to human readable format (B, KB, MB, GB, TB, PB)
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024:
            return f"{size_in_bytes:.1f} {unit}"
        size_in_bytes /= 1024
    return f"{size_in_bytes:.1f} PB"

def get_unique_field_values(mq, index_name, field, limit=1000):
    # Get unique values for a given field from the index
    results = mq.index(index_name).search(
        "*",
        limit=limit,
        searchable_attributes=["searchable_content"],
        show_highlights=False,
        attributes_to_retrieve=[field]
    )
    
    values = set()
    for hit in results['hits']:
        field_value = hit.get(field, [])
        
        if isinstance(field_value, list):
            for value in field_value:
                if value and value != "Not specified":
                    values.add(value)
        elif field_value and field_value != "Not specified":
            values.add(field_value)
    
    return sorted(list(values))

def search_datasets(query, filters=None, limit=10):
    mq = marqo.Client(url='http://localhost:8882')
    
    filter_conditions = []
    if filters:
        if filters.get('modality'):
            filter_conditions.append(f"modalities:{filters['modality']}")
        if filters.get('min_size') is not None:
            filter_conditions.append(f"size:[{filters['min_size']} TO *]")
        if filters.get('max_size') is not None:
            filter_conditions.append(f"size:[* TO {filters['max_size']}]")
        if filters.get('species'):
            filter_conditions.append(f"species:(*{filters['species']}*)")
        if filters.get('tasks'):
            filter_conditions.append(f"tasks:{filters['tasks']}")
            
    filter_string = " AND ".join(filter_conditions) if filter_conditions else None
    
    if filter_string:
        st.sidebar.write("Active filters:", filter_string)
    
    results = mq.index("openneuro_datasets").search(
        query if query else "*",
        limit=limit,
        filter_string=filter_string
    )
    return results["hits"]

def format_array_field(value):
    # Convert array to comma-separated string
    if isinstance(value, list):
        return ", ".join(value)
    return str(value)

def format_dataset_url(dataset_id: str) -> str:
    # Format OpenNeuro dataset URL
    if dataset_id and dataset_id != "Not specified":
        return f"https://openneuro.org/datasets/{dataset_id}"
    return "#"

def get_filter_options_from_results(results):
    # Extract unique filter values from search results
    modalities = set()
    species = set()
    tasks = set()
    
    for result in results:
        if isinstance(result.get('modalities'), list):
            for m in result['modalities']:
                if m and m != "Not specified":
                    modalities.add(m)
                    
        if result.get('species') and result['species'] != "Not specified":
            species.add(result['species'])
            
        if isinstance(result.get('tasks'), list):
            for t in result['tasks']:
                if t and t != "Not specified":
                    tasks.add(t)
    
    return {
        'modalities': sorted(list(modalities)),
        'species': sorted(list(species)),
        'tasks': sorted(list(tasks))
    }

@st.cache_data(ttl=3600)
def get_all_filter_options():
    # Get all available filter options from the index
    mq = marqo.Client(url='http://localhost:8882')
    return {
        'modalities': get_unique_field_values(mq, "openneuro_datasets", "modalities"),
        'species': get_unique_field_values(mq, "openneuro_datasets", "species"),
        'tasks': get_unique_field_values(mq, "openneuro_datasets", "tasks")
    }

def main():
    st.title("Neuroscience Dataset Search")
    mq = marqo.Client(url='http://localhost:8882')
    index_stats = mq.index("neuroscience_datasets").get_stats()
    st.markdown(f"Search a list of :blue[**{index_stats['numberOfDocuments']}**] neuroscience datasets from OpenNeuro, DANDI, and more using natural language.")
    
    # Search interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_input("Search datasets", placeholder="Enter keywords, modalities, species, etc.")
    
    with col2:
        limit = st.number_input("Results limit", min_value=1, max_value=100, value=10)
    
    # Get initial results without filters
    initial_results = search_datasets("dataset", None, limit)
    
    # Get filter options - use all options if no results
    if query == "":
        filter_options = get_all_filter_options()
    else:
        filter_options = get_filter_options_from_results(initial_results)
    # Filters
    st.sidebar.header("Filters")
    
    # Dropdown filters
    modality = st.sidebar.selectbox(
        "Modality",
        options=[""] + filter_options['modalities'],
        format_func=lambda x: "All Modalities" if x == "" else x
    )
    
    species = st.sidebar.selectbox(
        "Species",
        options=[""] + filter_options['species'],
        format_func=lambda x: "All Species" if x == "" else x
    )
    
    tasks = st.sidebar.selectbox(
        "Tasks",
        options=[""] + filter_options['tasks'],
        format_func=lambda x: "All Tasks" if x == "" else x
    )
    
    # Size filter
    st.sidebar.subheader("Dataset Size")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        min_size = st.number_input(
            "Min Size (GB)", 
            min_value=0.0, 
            value=0.0,
            step=1.0  # Increment by 1 GB
        )
    with col2:
        max_size = st.number_input(
            "Max Size (GB)", 
            min_value=0.0, 
            value=0.0,  # Default to 0 (no limit)
            step=1.0,  # Increment by 1 GB
            help="Set to 0 for no maximum limit"
        )
    
    # Convert GB to bytes for filtering
    min_size_bytes = int(min_size * 1_000_000_000)
    # Only use max_size if it's greater than 0
    max_size_bytes = int(max_size * 1_000_000_000) if max_size > 0 else None
    
    # Build filters dict
    filters = {}
    if modality:
        filters['modality'] = modality
    if species:
        filters['species'] = species
    if tasks:
        filters['tasks'] = tasks
    if min_size > 0:
        filters['min_size'] = min_size_bytes
    if max_size > 0:  # Only add max size if it's greater than 0
        filters['max_size'] = max_size_bytes
    
    # Get filtered results
    if query or filters:
        results = search_datasets(query if query else "*", filters, limit)
        
        if not results:
            st.warning("No results found matching your criteria.")
        
        # Display results
        for result in results:
            with st.container():
                # Format URL from dataset ID
                dataset_url = format_dataset_url(result['id'])
                st.markdown(f"### [{result['dataset_name']}]({dataset_url})")
                st.markdown(f"**ID**: {result['id']}")
                
                # Display metadata
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write("**Modalities:**", format_array_field(result['modalities']))
                    if result.get('species'):
                        st.write("**Species:**", result['species'])
                with col2:
                    if result.get('doi'):
                        st.write("**DOI:**", result['doi'])
                    st.write("**Published:**", result['publish_date'])
                with col3:
                    st.write("**Size:**", format_size(result['size']))
                    st.write("**Tasks:**", format_array_field(result['tasks']))
                
                # Show readme preview if available
                if result.get('readme'):
                    with st.expander("Show README"):
                        preview = result['readme'][:500] + "..." if len(result['readme']) > 500 else result['readme']
                        readme_container = st.empty()
                        readme_container.text(preview)
                        if len(result['readme']) > 500:
                            if st.button("Show Full README", key=f"readme_{result['id']}"):
                                readme_container.text(result['readme'])
                st.markdown("---")

if __name__ == "__main__":
    main() 