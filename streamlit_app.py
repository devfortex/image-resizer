import streamlit as st
import zipfile
import io
from PIL import Image, ImageOps, ImageFilter

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

st.markdown("### Resize Settings")
resize_mode = st.radio(
    "How should aspect ratio differences be handled?",
    options=["blur", "panorama", "crop", "stretch"],
    format_func=lambda x: {
        "blur": "🖼️ Smart Fit (Add blurred background to prevent content loss)",
        "panorama": "🔗 Panorama (Stitch files, fit, and slice to preserve continuous background)",
        "crop": "✂️ Fill Screen (Crop edges to fill exactly)",
        "stretch": "🔲 Stretch (Ignore aspect ratio completely)"
    }[x]
)

if uploaded_files and platforms_selected:
    if st.button("Resize and Create ZIP", type="primary"):
        with st.spinner("Resizing images..."):
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for platform in platforms_selected:
                    width, height = PLATFORMS[platform]
                    
                    if resize_mode == "panorama":
                        try:
                            # 1. Sort files
                            files = sorted(uploaded_files, key=lambda f: f.name)
                            N = len(files)
                            
                            # 2. Open all images
                            images = [Image.open(f).convert("RGB") for f in files]
                            
                            # 3. Stitch them seamlessly horizontally
                            total_w = sum(i.size[0] for i in images)
                            max_h = max(i.size[1] for i in images)
                            stitched = Image.new('RGB', (total_w, max_h))
                            x_offset = 0
                            for img in images:
                                stitched.paste(img, (x_offset, 0))
                                x_offset += img.size[0]
                                
                            # 4. Target canvas size for all slices
                            canvas_w = N * width
                            canvas_h = height
                            
                            # 5. Create background (blurred version of stitched image)
                            bg = ImageOps.fit(stitched, (canvas_w, canvas_h), method=Image.LANCZOS)
                            bg = bg.filter(ImageFilter.GaussianBlur(50))
                            
                            # 6. Create foreground (fit stitched image inside bounds completely)
                            fg = ImageOps.contain(stitched, (canvas_w, canvas_h), method=Image.LANCZOS)
                            
                            # 7. Paste foreground on blurred background
                            x = (canvas_w - fg.size[0]) // 2
                            y = (canvas_h - fg.size[1]) // 2
                            bg.paste(fg, (x, y))
                            
                            # 8. Slice back into individual screens and save
                            for i in range(N):
                                left = i * width
                                img_slice = bg.crop((left, 0, left + width, height))
                                
                                img_byte_arr = io.BytesIO()
                                img_slice.save(img_byte_arr, format="PNG", optimize=False)
                                img_byte_arr.seek(0)
                                
                                zip_path = f"{platform}/{files[i].name}"
                                zip_file.writestr(zip_path, img_byte_arr.read())
                        except Exception as e:
                            st.error(f"Error processing panorama: {e}")
                    else:
                        for uploaded_file in uploaded_files:
                            try:
                                img = Image.open(uploaded_file).convert("RGB")
                                
                                if resize_mode == "blur":
                                    # Fit image into the background completely and blur
                                    bg = ImageOps.fit(img, (width, height), method=Image.LANCZOS)
                                    bg = bg.filter(ImageFilter.GaussianBlur(30))
                                    
                                    # Scale foreground to fit inside bounds
                                    fg = ImageOps.contain(img, (width, height), method=Image.LANCZOS)
                                    
                                    # Center foreground on background
                                    x = (width - fg.size[0]) // 2
                                    y = (height - fg.size[1]) // 2
                                    bg.paste(fg, (x, y))
                                    resized_img = bg
                                    
                                elif resize_mode == "crop":
                                    resized_img = ImageOps.fit(img, (width, height), method=Image.LANCZOS, centering=(0.5, 0.5))
                                    
                                else: # stretch
                                    resized_img = img.resize((width, height), Image.LANCZOS)
                                
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
