import streamlit as st
import marqo
from collections import defaultdict

def format_size(size_in_bytes):
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024:
            return f"{size_in_bytes:.1f} {unit}"
        size_in_bytes /= 1024
    return f"{size_in_bytes:.1f} PB"

def get_unique_field_values(mq, index_name, field, limit=1000):
    """Get unique values for a field from the index"""
    results = mq.index(index_name).search(
        "*",  # Search all documents
        limit=limit,
        searchable_attributes=["searchable_content"],  # Search in the combined field
        show_highlights=False,
        attributes_to_retrieve=[field]  # Only retrieve the field we want
    )
    
    # Extract unique values
    values = set()
    for hit in results['hits']:
        field_value = hit.get(field, '')
        if field_value and field_value != 'Field not specified':
            if ',' in field_value:
                # Split comma-separated values and add each
                values.update(v.strip() for v in field_value.split(','))
            else:
                values.add(field_value)
    
    return sorted(list(values))

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_filter_options():
    """Load all filter options from the index"""
    mq = marqo.Client(url='http://localhost:8882')
    
    try:
        return {
            'modalities': get_unique_field_values(mq, "openneuro_datasets", "modalities"),
            'species': get_unique_field_values(mq, "openneuro_datasets", "species"),
            'tasks': get_unique_field_values(mq, "openneuro_datasets", "tasks")
        }
    except Exception as e:
        st.error(f"Error loading filter options: {str(e)}")
        return defaultdict(list)

def search_datasets(query, filters=None, limit=10):
    mq = marqo.Client(url='http://localhost:8882')
    
    # Build filter conditions
    filter_conditions = []
    if filters:
        if filters.get('modality'):
            # Filter for array field
            filter_conditions.append(f"modalities:{filters['modality']}")
        if filters.get('min_size') is not None:
            filter_conditions.append(f"size:[{filters['min_size']} TO *]")
        if filters.get('max_size') is not None:
            filter_conditions.append(f"size:[* TO {filters['max_size']}]")
        if filters.get('species'):
            filter_conditions.append(f"species:(*{filters['species']}*)")
        if filters.get('tasks'):
            # Filter for array field
            filter_conditions.append(f"tasks:{filters['tasks']}")
            
    filter_string = " AND ".join(filter_conditions) if filter_conditions else None
    
    # Debug print
    if filter_string:
        st.sidebar.write("Active filters:", filter_string)
    
    results = mq.index("openneuro_datasets").search(
        query if query else "*",
        limit=limit,
        filter_string=filter_string
    )
    return results["hits"]

def format_array_field(value):
    """Format array field for display"""
    if isinstance(value, list):
        return ", ".join(value)
    return str(value)

def format_dataset_url(dataset_id: str) -> str:
    """Format OpenNeuro dataset URL from ID"""
    if dataset_id and dataset_id != "Not specified":
        return f"https://openneuro.org/datasets/{dataset_id}"
    return "#"

def main():
    st.title("OpenNeuro Dataset Search")
    st.write("Search through neuroscience datasets from OpenNeuro using natural language")
    
    # Load filter options
    try:
        filter_options = load_filter_options()
    except Exception as e:
        st.error(f"Error loading filter options: {e}")
        filter_options = defaultdict(list)
    
    # Search and filter interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_input("Search datasets", placeholder="Enter keywords, modalities, species, etc.")
    
    with col2:
        limit = st.number_input("Results limit", min_value=1, max_value=100, value=10)
    
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
    
    if query:
        results = search_datasets(query, filters, limit)
        
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