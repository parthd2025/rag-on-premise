"""
Script to download models from Hugging Face for on-premise use
"""
import os
import sys
from pathlib import Path
from huggingface_hub import snapshot_download
from sentence_transformers import SentenceTransformer

def download_embedding_model(model_name: str, local_path: str):
    """Download embedding model from Hugging Face"""
    print(f"\n📥 Downloading embedding model: {model_name}")
    print(f"   Destination: {local_path}")
    
    try:
        # Create directory
        Path(local_path).mkdir(parents=True, exist_ok=True)
        
        # Download using sentence-transformers (handles everything)
        print("   Loading model (this will download if not cached)...")
        model = SentenceTransformer(model_name)
        
        # Save to local path
        print(f"   Saving to {local_path}...")
        model.save(local_path)
        
        print(f"✅ Embedding model downloaded successfully!")
        print(f"   Location: {local_path}")
        return True
    except Exception as e:
        print(f"❌ Error downloading embedding model: {e}")
        return False

def download_llm_model(model_name: str, local_path: str):
    """Download LLM model from Hugging Face for vLLM"""
    print(f"\n📥 Downloading LLM model: {model_name}")
    print(f"   Destination: {local_path}")
    print("   This may take a while (7B models are ~15GB)...")
    
    try:
        # Create directory
        Path(local_path).mkdir(parents=True, exist_ok=True)
        
        # Download using huggingface_hub
        print("   Downloading from Hugging Face Hub...")
        snapshot_download(
            repo_id=model_name,
            local_dir=local_path,
            local_dir_use_symlinks=False,
            resume_download=True
        )
        
        print(f"✅ LLM model downloaded successfully!")
        print(f"   Location: {local_path}")
        return True
    except Exception as e:
        print(f"❌ Error downloading LLM model: {e}")
        return False

def main():
    """Main function to download all models"""
    print("=" * 60)
    print("RAG ON PREMISE - Model Download Script")
    print("=" * 60)
    
    # Get models directory from config or use default
    models_dir = os.getenv("MODELS_DIR", "./models")
    models_path = Path(models_dir)
    models_path.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📁 Models will be stored in: {models_path.absolute()}")
    
    # Embedding model
    embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_path = models_path / "embedding" / "all-MiniLM-L6-v2"
    
    # LLM model
    llm_model = "mistralai/Mistral-7B-Instruct-v0.2"
    llm_path = models_path / "llm" / "Mistral-7B-Instruct-v0.2"
    
    print("\n" + "=" * 60)
    print("Models to download:")
    print(f"  1. Embedding: {embedding_model} (~90MB)")
    print(f"  2. LLM: {llm_model} (~15GB)")
    print("=" * 60)
    
    response = input("\nProceed with download? (y/n): ").strip().lower()
    if response != 'y':
        print("Download cancelled.")
        return
    
    # Download embedding model
    success_embedding = download_embedding_model(embedding_model, str(embedding_path))
    
    # Download LLM model
    print("\n" + "=" * 60)
    print("⚠️  LLM model download is large (~15GB)")
    print("   This will take time depending on your internet speed")
    print("=" * 60)
    
    response = input("\nDownload LLM model? (y/n): ").strip().lower()
    success_llm = False
    if response == 'y':
        success_llm = download_llm_model(llm_model, str(llm_path))
    else:
        print("Skipping LLM model download. You can download it later.")
    
    # Summary
    print("\n" + "=" * 60)
    print("Download Summary:")
    print("=" * 60)
    print(f"Embedding Model: {'✅ Downloaded' if success_embedding else '❌ Failed'}")
    print(f"  Path: {embedding_path}")
    print(f"LLM Model: {'✅ Downloaded' if success_llm else '⏭️  Skipped'}")
    print(f"  Path: {llm_path}")
    
    if success_embedding:
        print("\n📝 Next steps:")
        print(f"1. Update your .env file:")
        print(f"   EMBEDDING_MODEL_PATH={embedding_path.absolute()}")
        if success_llm:
            print(f"   VLLM_MODEL_PATH={llm_path.absolute()}")
        print("\n2. When starting vLLM, use:")
        if success_llm:
            print(f"   vllm serve {llm_path.absolute()} --port 8001")
        else:
            print(f"   vllm serve {llm_model} --port 8001")
        print("\n3. Restart your backend server")

if __name__ == "__main__":
    main()

