import io
import streamlit as st
from docx import Document

from src.detectors import RegexDetector, NERDetector
from src.replacement_engine import redact_paragraph
from src.docx_reader import iter_paragraphs
from src import fake_generator

# Page Config
st.set_page_config(
    page_title="PII Guardian — Anonymization Web App",
    page_icon="🛡️",
    layout="wide",
)

# Custom Sleek Styling
st.markdown(
    """
    <style>
    .main {
        background-color: #0f1115;
        color: #e2e8f0;
    }
    h1, h2, h3 {
        color: #6366f1 !important;
    }
    .stButton>button {
        background-color: #6366f1;
        color: white;
        border-radius: 6px;
        padding: 0.5rem 1.5rem;
        border: none;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #4f46e5;
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def load_detectors():
    """Cache the detectors to avoid reloading spaCy en_core_web_lg on every run."""
    with st.spinner("Initializing AI Detection Models (this takes ~10 seconds on first startup)..."):
        regex = RegexDetector()
        ner = NERDetector()
    return [regex, ner]


def main():
    st.title("🛡️ PII Guardian — Anonymizer Engine")
    st.write(
        "Upload any `.docx` file containing sensitive data to detect PII "
        "and replace it with realistic fake values while fully preserving formatting."
    )

    detectors = load_detectors()

    # Sidebar Panel
    st.sidebar.header("Navigation & Upload")
    uploaded_file = st.sidebar.file_uploader("Choose a DOCX file", type=["docx"])

    if not uploaded_file:
        # Clear session state if file is removed
        st.session_state.pop("processed_doc", None)
        st.session_state.pop("all_detected", None)
        st.session_state.pop("cache_map", None)
        st.session_state.pop("paragraphs_count", None)

        st.info("👈 Upload a `.docx` file using the sidebar to get started.")
        st.markdown(
            """
            ### Features
            *   **Hybrid Detection Pipeline**: Uses Regex for structured fields (emails, phones, credit cards, dates) and spaCy Large NER for names, companies, and locations.
            *   **Format-Preserving Replacement**: Modifies file text elements without breaking tables, fonts, bold, or italic styles.
            *   **Consistent Replacement Map**: Replaces duplicate occurrences of same PII with the same fake name/value throughout the document.
            """
        )
        return

    # Process Uploaded File
    st.success("File uploaded successfully!")
    file_details = {"FileName": uploaded_file.name, "FileType": uploaded_file.type}
    st.sidebar.json(file_details)

    # Initialize session states to persist outputs on click/download re-runs
    if "processed_doc" not in st.session_state:
        st.session_state.processed_doc = None
    if "all_detected" not in st.session_state:
        st.session_state.all_detected = None
    if "cache_map" not in st.session_state:
        st.session_state.cache_map = None
    if "paragraphs_count" not in st.session_state:
        st.session_state.paragraphs_count = None

    if st.sidebar.button("Run Redaction Engine"):
        # Reset Faker cache to ensure clean generation for each run
        fake_generator.reset_cache()

        # Read doc from memory buffer
        doc = Document(io.BytesIO(uploaded_file.read()))
        paragraphs = list(iter_paragraphs(doc))

        all_detected = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        status_text.text("Scanning document paragraphs...")
        
        # Process and collect detections
        for i, paragraph in enumerate(paragraphs):
            full_text = "".join(run.text for run in paragraph.runs)
            if not full_text.strip():
                continue

            # Accumulate entities found for UI reporting
            for detector in detectors:
                all_detected.extend(detector.detect(full_text))

            # Apply replacement in-place
            redact_paragraph(paragraph, detectors)

            # Update progress
            progress_bar.progress((i + 1) / len(paragraphs))

        status_text.text("Formatting complete!")
        progress_bar.empty()

        # Save redacted document back to a memory buffer for download
        output_buffer = io.BytesIO()
        doc.save(output_buffer)
        output_buffer.seek(0)

        # Store in session state
        st.session_state.processed_doc = output_buffer.getvalue()
        st.session_state.all_detected = all_detected
        st.session_state.cache_map = dict(fake_generator._cache)
        st.session_state.paragraphs_count = len(paragraphs)

    # Render results if we have processed data in session state
    if st.session_state.processed_doc is not None:
        # Metric Cards Layout
        st.header("⚡ Processing Summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Paragraphs Processed", value=st.session_state.paragraphs_count)
        with col2:
            st.metric(label="Total PII Found", value=len(st.session_state.all_detected))
        with col3:
            st.metric(label="Unique Replaced Entities", value=len(st.session_state.cache_map))

        # Show mappings and details in tabs
        tab1, tab2 = st.tabs(["Replacements Map", "Sample Preview"])

        with tab1:
            st.subheader("Exact Replacement Mapping Table")
            if st.session_state.cache_map:
                mappings = [
                    {"Original PII": orig, "Anonymized Replacement": fake_val}
                    for orig, fake_val in st.session_state.cache_map.items()
                ]
                st.dataframe(mappings, use_container_width=True)
            else:
                st.write("No PII detected in this document.")

        with tab2:
            st.subheader("PII Detection Breakdown")
            if st.session_state.all_detected:
                preview_list = [
                    {"PII Value": e["text"], "Entity Type": e["type"]}
                    for e in st.session_state.all_detected[:50]
                ]
                st.dataframe(preview_list, use_container_width=True)
                if len(st.session_state.all_detected) > 50:
                    st.caption("Showing the first 50 detections.")
            else:
                st.write("No detections to display.")

        # Download Panel
        st.divider()
        st.subheader("💾 Export Document")
        st.download_button(
            label="Download Redacted DOCX",
            data=st.session_state.processed_doc,
            file_name=f"redacted_{uploaded_file.name}",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )


if __name__ == "__main__":
    main()
