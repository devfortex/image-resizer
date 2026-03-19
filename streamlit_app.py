import streamlit as st
import zipfile
import io
from PIL import Image, ImageOps

# Platform configs: (width, height)
PLATFORMS = {
    "ios": (1242, 2688),       # iPhone 6.5" — App Store
    "android": (1080, 1920),   # 9:16 — Google Play Store
}

st.set_page_config(page_title="Image Resizer for App Stores", page_icon="📱")

st.title("📱 App Store & Play Store Image Resizer")
st.write("Upload your PNG screenshots to resize them for iOS (1242×2688) and/or Android (1080×1920, 9:16) and download them instantly as a ZIP file.")

uploaded_files = st.file_uploader("Choose PNG images", type=["png"], accept_multiple_files=True)

platforms_selected = st.multiselect(
    "Select target platforms",
    options=list(PLATFORMS.keys()),
    default=list(PLATFORMS.keys()),
    format_func=lambda x: "iOS (1242×2688)" if x == "ios" else "Android (1080×1920)"
)

if uploaded_files and platforms_selected:
    if st.button("Resize and Create ZIP", type="primary"):
        with st.spinner("Resizing images..."):
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for platform in platforms_selected:
                    width, height = PLATFORMS[platform]
                    
                    for uploaded_file in uploaded_files:
                        try:
                            img = Image.open(uploaded_file)
                            # Resize using LANCZOS with center crop
                            resized_img = ImageOps.fit(img, (width, height), method=Image.LANCZOS, centering=(0.5, 0.5))
                            
                            # Save to BytesIO
                            img_byte_arr = io.BytesIO()
                            resized_img.save(img_byte_arr, format="PNG", optimize=False)
                            img_byte_arr.seek(0)
                            
                            # Define path in zip: platform/filename
                            zip_path = f"{platform}/{uploaded_file.name}"
                            zip_file.writestr(zip_path, img_byte_arr.read())
                        except Exception as e:
                            st.error(f"Error processing {uploaded_file.name}: {e}")
        
            zip_buffer.seek(0)
            
            st.success(f"✅ Successfully resized {len(uploaded_files)} image(s) for {len(platforms_selected)} platform(s)!")
            st.download_button(
                label="⬇️ Download Resized Images (ZIP)",
                data=zip_buffer,
                file_name="resized_screenshots.zip",
                mime="application/zip",
                type="primary"
            )
elif not uploaded_files:
    st.info("👆 Please upload at least one PNG image to get started.")
elif not platforms_selected:
    st.warning("⚠️ Please select at least one target platform.")

