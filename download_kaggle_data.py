import kagglehub
import os
import shutil

def download_dataset():
    try:
        # Candidate 4: Ken Jee's dataset (Educational, likely open)
        slug = "kenjee/ken-jee-youtube-data"
        print(f"⬇️ Attempting to download '{slug}'...")
        
        path = kagglehub.dataset_download(slug)
        
        print(f"✅ Download successful!")
        print(f"   Cache Path: {path}")
        
        # Verify content
        files = os.listdir(path)
        print(f"   Files found: {files}")
        
        # Move to workspace
        workspace_dir = "/Users/yvesromano/AiRAG/training_data/external"
        os.makedirs(workspace_dir, exist_ok=True)
        
        csv_count = 0
        for f in files:
            if f.endswith('.csv'):
                src = os.path.join(path, f)
                dst = os.path.join(workspace_dir, f)
                shutil.copy2(src, dst)
                print(f"   📦 Copied '{f}' to {workspace_dir}")
                csv_count += 1
                
        if csv_count > 0:
            print(f"✅ Successfully imported {csv_count} dataset files.")
    except Exception as e:
        print(f"\n❌ Error downloading dataset: {e}")
        if "404" in str(e):
             print("\n⚠️ Dataset not found. Slug might be incorrect.")
        elif "403" in str(e):
             print("\n⚠️ Authentication required for this dataset.")

if __name__ == "__main__":
    download_dataset()
