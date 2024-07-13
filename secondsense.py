import streamlit as st
import pandas as pd
import re
import io
from PIL import Image
import google.generativeai as genai

# Browser site format
st.set_page_config(
    page_title="SecondSense",
    page_icon="SecondSensefavicon.ico"
)

# Configure the API key
GOOGLE_API_KEY = 'YourApiKey'
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize the Gemini model
model = genai.GenerativeModel('models/gemini-1.5-flash')

# Function to process images and extract details
def process_images(image_files):
    details = {
        'Garment Type': [],
        'Brand': [],
        'Size': [],
        'Color': [],
        'Fabric': [],
        'Additional Characteristics': [],
        'Image': [],
        'Text': []
    }

    combined_image = combine_images(image_files)
    text = get_text_from_image(combined_image)

    garment_type, brand, size, color, fabric, additional_characteristics = extract_garment_details(text)
    details['Garment Type'].append(garment_type)
    details['Brand'].append(brand)
    details['Size'].append(size)
    details['Color'].append(color)
    details['Fabric'].append(fabric)
    details['Additional Characteristics'].append(additional_characteristics)
    details['Image'].append(combined_image)
    details['Text'].append(text)

    return pd.DataFrame(details), combined_image

def combine_images(image_files):
    images = [Image.open(image_file) for image_file in image_files]
    widths, heights = zip(*(image.size for image in images))

    total_width = sum(widths)
    max_height = max(heights)

    combined_image = Image.new('RGB', (total_width, max_height))

    x_offset = 0
    for image in images:
        combined_image.paste(image, (x_offset, 0))
        x_offset += image.width

    return combined_image

def get_text_from_image(image):
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG')
    image_data = img_byte_arr.getvalue()
    
    # Convert the image data to the appropriate format for the API
    image_part = {
        "inline_data": {
            "data": image_data,
            "mime_type": "image/jpeg"
        }
    }
    
    # Generate content from the image using the Gemini API
    response = model.generate_content([
        "Describe the garment in the image and provide the following details:",
        "Garment Type:",
        "Brand:",
        "Size:",
        "Color:",
        "Fabric:",
        "Additional Characteristics:",
        image_part
    ])
    
    if response and response.candidates:
        return response.candidates[0].content.parts[0].text
    return 'Text not found'

def extract_garment_details(text):
    # Print the raw text to see the actual format
    st.write(text)
    
    # Patterns for structured responses
    structured_patterns = {
        'Garment Type': re.search(r'Garment Type:\s*(.*)', text),
        'Brand': re.search(r'Brand:\s*(.*)', text),
        'Size': re.search(r'Size:\s*(.*)', text),
        'Color': re.search(r'Color:\s*(.*)', text),
        'Fabric': re.search(r'Fabric:\s*(.*)', text),
        'Additional Characteristics': re.search(r'Additional Characteristics:\s*(.*)', text)
    }

    if all(pattern is not None for pattern in structured_patterns.values()):
        garment_type = clean_text(structured_patterns['Garment Type'].group(1))
        brand = clean_text(structured_patterns['Brand'].group(1))
        size = clean_text(structured_patterns['Size'].group(1))
        color = clean_text(structured_patterns['Color'].group(1))
        fabric = clean_text(structured_patterns['Fabric'].group(1))
        additional_characteristics = clean_text(structured_patterns['Additional Characteristics'].group(1))

        return garment_type, brand, size, color, fabric, additional_characteristics

    # Patterns for unstructured responses
    garment_type = re.search(r'\b(zip-up hoodie|hoodie|shirt|t-shirt|jacket|pants|shorts|sweater|dress|skirt|sweatshirt)\b', text, re.IGNORECASE)
    brand = re.search(r'brand is ([A-Za-z\s]+)', text, re.IGNORECASE) or re.search(r'\"([^\"]+)\"', text, re.IGNORECASE)
    size = re.search(r'\b(size \w+|\bL\b|\bM\b|\bS\b|\bXL\b|\bXXL\b)\b', text, re.IGNORECASE)
    color = re.search(r'\b(gray|red|blue|green|black|white|yellow|brown|purple|pink|orange|beige)\b', text, re.IGNORECASE)
    fabric = re.search(r'(\d+% \w+)', text, re.IGNORECASE)
    additional_characteristics = re.findall(r'(\bhood\b|\bstring\b|\btag\b|\bembroidered\b|\bkangaroo pocket\b|\blabel\b|\btext\b|\blining\b|\blogo\b|\bpocket\b)', text, re.IGNORECASE)

    return (
        garment_type.group(1) if garment_type else 'N/A',
        brand.group(1) if brand else 'N/A',
        size.group(1) if size else 'N/A',
        color.group(1) if color else 'N/A',
        fabric.group(1) if fabric else 'N/A',
        ', '.join(additional_characteristics) if additional_characteristics else 'N/A'
    )

def clean_text(text):
    cleaned_text = text.replace('**', '').strip()  
    return cleaned_text

def main():
    st.title("Garment Detail Extractor")

    # Initialize session state variables
    if 'garment_type' not in st.session_state:
        st.session_state.garment_type = ""
    if 'brand' not in st.session_state:
        st.session_state.brand = ""
    if 'size' not in st.session_state:
        st.session_state.size = ""
    if 'color' not in st.session_state:
        st.session_state.color = ""
    if 'fabric' not in st.session_state:
        st.session_state.fabric = ""
    if 'additional_characteristics' not in st.session_state:
        st.session_state.additional_characteristics = ""
    if 'images' not in st.session_state:
        st.session_state.images = []
    if 'df' not in st.session_state:
        st.session_state.df = None

    uploaded_files = st.file_uploader("Upload Images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

    if uploaded_files:
        df, combined_image = process_images(uploaded_files)
        st.session_state.df = df

        # Drop the 'Image' and 'Text' columns
        df_display = df.drop(columns=['Image', 'Text'], errors='ignore')
        
        st.write(df_display)

        output = io.BytesIO()
        df.to_excel(output, index=False, engine='xlsxwriter')
        output.seek(0)

        st.download_button(
            label="Download Excel",
            data=output,
            file_name="garment_details.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Store the extracted details and images in session state
        st.session_state.garment_type = df['Garment Type'][0]
        st.session_state.brand = df['Brand'][0]
        st.session_state.size = df['Size'][0]
        st.session_state.color = df['Color'][0]
        st.session_state.fabric = df['Fabric'][0]
        st.session_state.additional_characteristics = df['Additional Characteristics'][0]
        st.session_state.images = uploaded_files

        # Implement the manual input mechanism if there are N/A values
        manual_inputs = {}

        for column in df.columns:
            if df.iloc[0][column] == 'N/A':
                value = st.text_input(f"Input {column}", value="")
                manual_inputs[column.lower().replace(" ", "_")] = value

        # Garment Quality input
        quality = st.text_input("Garment Quality", value="")
        manual_inputs["garment_quality"] = quality
        
        # Store manual inputs in session state
        for key, value in manual_inputs.items():
            st.session_state[key] = value

        confirm_button = st.button("Confirm Item")

        if confirm_button:
            # Update the dataframe with the manually inputted values
            for column in manual_inputs:
                session_key = column.replace(" ", "_")
                if session_key in st.session_state:
                    st.session_state.df.at[0, column.replace("_", " ").title()] = st.session_state[session_key]

            # Display the updated dataframe with editable input fields, excluding 'Image' and 'Text'
            updated_df = st.session_state.df.drop(columns=['Image', 'Text'], errors='ignore')
            
            # Add some blank space
            st.markdown("<br><br><br>", unsafe_allow_html=True)

            # Set background color for the updated details section
            st.markdown("""
                <style>
                    .updated-details {
                        background-color: lightblue;
                        padding: 20px;
                        border-radius: 10px;
                    }
                </style>
                """, unsafe_allow_html=True)

            # Display updated details with background color
            st.markdown('<div class="updated-details">', unsafe_allow_html=True)#

            st.write("## Information for Take-Back Company")
            for column in updated_df.columns:
                st.text_input(column, value=updated_df.at[0, column])
            st.markdown('</div>', unsafe_allow_html=True)#

            st.write("Uploaded Images:")
            #for image_file in st.session_state.images:
                ##image = Image.open(image_file)
                #st.image(image, caption="Uploaded Image", width=150, use_column_width=False)
                #st.write("## Confirmed Images")
            st.image(combined_image)

if __name__ == "__main__":
    main()

