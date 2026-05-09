import os
import uuid
from django.conf import settings
from django.core.files.storage import default_storage


def save_uploaded_files(uploaded_images, user_id):
    """Save uploaded images and return list of file paths"""
    image_paths = []
    
    print(f"🔍 save_uploaded_files called with user_id: {user_id}")
    print(f"🔍 uploaded_images count: {len(uploaded_images) if uploaded_images else 0}")
    
    # Create user-specific folder
    folder_path = os.path.join('blog_uploads', user_id)
    full_folder_path = os.path.join(settings.MEDIA_ROOT, folder_path)
    os.makedirs(full_folder_path, exist_ok=True)
    print(f"📁 Folder path: {full_folder_path}")
    
    for idx, image in enumerate(uploaded_images):
        print(f"📷 Processing image {idx}: {image.name}, size: {image.size if hasattr(image, 'size') else 'unknown'}")
        
        # Generate unique filename
        ext = image.name.split('.')[-1] if '.' in image.name else 'jpg'
        filename = f"{uuid.uuid4().hex}.{ext}"
        file_path = os.path.join(folder_path, filename)
        
        print(f"💾 Saving to: {file_path}")
        
        # Save file
        try:
            saved_path = default_storage.save(file_path, image)
            image_paths.append(saved_path)
            print(f"✅ Saved image: {saved_path}")
        except Exception as e:
            print(f"❌ Error saving image: {e}")
    
    return image_paths