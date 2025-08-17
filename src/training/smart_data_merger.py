import os
import pandas as pd
import glob
from datetime import datetime
import json
import shutil


class SmartDataMerger:
    """Handles intelligent merging of CRM data with fresh API data"""
    
    def __init__(self, project_root=None):
        if project_root is None:
            self.project_root = os.path.join(os.path.dirname(__file__), "..", "..")
        else:
            self.project_root = project_root
            
        self.crm_data_path = os.path.join(self.project_root, "data", "raw", "crm_labled.csv")
        self.adapted_dir = os.path.join(self.project_root, "data", "adapted")
        self.training_dir = os.path.join(self.project_root, "data", "training")
        self.metadata_dir = os.path.join(self.project_root, "metadata")
        
        # Define the exact features for model training
        self.training_features = [
            'lead_id', 'company_size', 'source', 'region', 'contact_attempts',
            'days_since_first_contact', 'job_title', 'has_company_website', 'converted'
        ]
        
        # Ensure directories exist
        os.makedirs(self.training_dir, exist_ok=True)
        os.makedirs(self.metadata_dir, exist_ok=True)
    
    def load_crm_data(self):
        """Load historical CRM data and filter to training features"""
        try:
            crm_data = pd.read_csv(self.crm_data_path)
            print(f" Loaded CRM data: {len(crm_data)} records")
            
            # Filter to only training features (keep available columns)
            available_features = [col for col in self.training_features if col in crm_data.columns]
            crm_data = crm_data[available_features]
            
            print(f" Filtered to {len(available_features)} training features: {available_features}")
            
            return crm_data
        except Exception as e:
            print(f" Error loading CRM data: {e}")
            return None
    
    def load_fresh_data(self):
        """Load all fresh labeled data from adapted directory and filter to training features"""
        labeled_files = glob.glob(os.path.join(self.adapted_dir, "labeled_leads_*.csv"))
        
        if not labeled_files:
            print(" No fresh labeled data found")
            return None
        
        print(f" Found {len(labeled_files)} fresh data files")
        
        fresh_data_list = []
        file_info = []
        
        for file_path in labeled_files:
            try:
                data = pd.read_csv(file_path)
                
                # Filter to only training features (keep available columns)
                available_features = [col for col in self.training_features if col in data.columns]
                data_filtered = data[available_features]
                
                fresh_data_list.append(data_filtered)
                
                # Extract timestamp from filename for tracking
                filename = os.path.basename(file_path)
                timestamp = filename.split('_')[-1].replace('.csv', '')
                
                file_info.append({
                    "file": filename,
                    "timestamp": timestamp,
                    "records": len(data_filtered),
                    "original_records": len(data),
                    "features_kept": len(available_features),
                    "path": file_path
                })
                
                print(f"   {filename}: {len(data_filtered)} records ({len(available_features)} training features)")
                
            except Exception as e:
                print(f" Error loading {file_path}: {e}")
        
        if fresh_data_list:
            combined_fresh = pd.concat(fresh_data_list, ignore_index=True)
            print(f" Total fresh data: {len(combined_fresh)} records")
            print(f" Training features in fresh data: {list(combined_fresh.columns)}")
            return combined_fresh, file_info
        
        return None, []
    
    def smart_deduplication(self, crm_data, fresh_data):
        """
        Intelligent deduplication with fresh data taking priority
        Uses lead_id or email as the primary key for deduplication
        """
        print("\n Starting Smart Deduplication...")
        
        # Determine deduplication key (prefer lead_id, fallback to email)
        dedup_key = None
        if 'lead_id' in crm_data.columns and 'lead_id' in fresh_data.columns:
            dedup_key = 'lead_id'
            print(" Using 'lead_id' for deduplication")
        elif 'email' in crm_data.columns and 'email' in fresh_data.columns:
            dedup_key = 'email'
            print(" Using 'email' for deduplication")
        else:
            print(" No common deduplication key found (lead_id or email), proceeding without deduplication")
            combined = pd.concat([crm_data, fresh_data], ignore_index=True)
            return combined, {"duplicates_removed": 0, "deduplication_method": "none", "dedup_key": "none"}
        
        # Add source tracking
        crm_data = crm_data.copy()
        fresh_data = fresh_data.copy()
        crm_data['data_source'] = 'crm_historical'
        fresh_data['data_source'] = 'api_fresh'
        
        # Combine all data
        combined = pd.concat([crm_data, fresh_data], ignore_index=True)
        initial_count = len(combined)
        
        print(f"Before deduplication: {initial_count} records")
        print(f"  - CRM historical: {len(crm_data)} records")
        print(f"  - Fresh API: {len(fresh_data)} records")
        
        # Sort by data_source (fresh data first) to ensure fresh data takes priority
        combined = combined.sort_values([dedup_key, 'data_source'], ascending=[True, True])
        
        # Remove duplicates, keeping first occurrence (which will be fresh data)
        duplicates_before = combined.duplicated(subset=[dedup_key]).sum()
        combined_deduplicated = combined.drop_duplicates(subset=[dedup_key], keep='first')
        
        final_count = len(combined_deduplicated)
        duplicates_removed = initial_count - final_count
        
        print(f" After deduplication: {final_count} records")
        print(f" Duplicates removed: {duplicates_removed}")
        
        # Calculate source distribution
        source_dist = combined_deduplicated['data_source'].value_counts().to_dict()
        print(f" Final distribution: {source_dist}")
        
        # Remove the tracking column
        combined_deduplicated = combined_deduplicated.drop('data_source', axis=1)
        
        dedup_stats = {
            "duplicates_removed": duplicates_removed,
            "deduplication_method": f"{dedup_key}_based",
            "dedup_key": dedup_key,
            "initial_count": initial_count,
            "final_count": final_count,
            "source_distribution": source_dist
        }
        
        return combined_deduplicated, dedup_stats
    
    def create_master_dataset(self, save_intermediate=True):
        """Create master training dataset with smart merging"""
        
        print(" Creating Master Training Dataset...")
        print("=" * 50)
        
        # Load data sources
        crm_data = self.load_crm_data()
        if crm_data is None:
            print(" Cannot proceed without CRM data")
            return None, None
        
        fresh_data, file_info = self.load_fresh_data()
        
        if fresh_data is None:
            print(" No fresh data found, using CRM data only")
            master_data = crm_data.copy()
            merge_stats = {
                "crm_records": len(crm_data),
                "fresh_records": 0,
                "final_records": len(master_data),
                "fresh_files": [],
                "deduplication": {"duplicates_removed": 0, "deduplication_method": "none"}
            }
        else:
            # Perform smart deduplication
            master_data, dedup_stats = self.smart_deduplication(crm_data, fresh_data)
            
            merge_stats = {
                "crm_records": len(crm_data),
                "fresh_records": len(fresh_data),
                "final_records": len(master_data),
                "fresh_files": file_info,
                "deduplication": dedup_stats
            }
        
        # Generate timestamp for versioning
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save master dataset
        master_filename = f"master_training_data_{timestamp}_production.csv"
        master_path = os.path.join(self.training_dir, master_filename)
        master_data.to_csv(master_path, index=False)
        
        print(f" Master dataset saved: {master_filename}")
        print(f" Final dataset: {len(master_data)} records")
        
        # Save merge metadata
        merge_metadata = {
            "created_at": datetime.now().isoformat(),
            "master_dataset_path": master_path,
            "master_dataset_filename": master_filename,
            "timestamp": timestamp,
            "merge_statistics": merge_stats
        }
        
        metadata_path = os.path.join(self.metadata_dir, f"merge_metadata_{timestamp}.json")
        with open(metadata_path, "w") as f:
            json.dump(merge_metadata, f, indent=2)
        
        # Save intermediate files if requested
        if save_intermediate:
            # Save feature extraction info based on training features
            available_features = [col for col in self.training_features if col in master_data.columns]
            
            feature_info = {
                "training_features_spec": self.training_features,
                "available_features": available_features,
                "feature_columns": list(master_data.columns),
                "target_column": "converted",
                "numeric_features": [col for col in ["contact_attempts", "days_since_first_contact", "has_company_website"] if col in master_data.columns],
                "categorical_features": [col for col in ["company_size", "source", "region", "job_title"] if col in master_data.columns],
                "id_column": "lead_id" if "lead_id" in master_data.columns else None,
                "dataset_timestamp": timestamp,
                "filtered_for_training": True
            }
            
            feature_path = os.path.join(self.training_dir, f"model_features_{timestamp}_production.csv")
            
            # Create a summary of features for reference
            feature_summary = pd.DataFrame({
                'feature_name': feature_info["feature_columns"],
                'feature_type': ['id' if col == 'lead_id'
                               else 'categorical' if col in feature_info["categorical_features"] 
                               else 'numeric' if col in feature_info["numeric_features"]
                               else 'target' if col == 'converted'
                               else 'other' for col in feature_info["feature_columns"]],
                'used_for_training': [col != 'lead_id' for col in feature_info["feature_columns"]]
            })
            
            feature_summary.to_csv(feature_path, index=False)
            print(f" Feature info saved: {os.path.basename(feature_path)}")
        
        return master_path, merge_metadata
    
    def cleanup_old_fresh_data(self, keep_latest=3):
        """Clean up old fresh data files, keeping only the latest ones"""
        
        print(f"\n Cleaning up old fresh data files (keeping latest {keep_latest})...")
        
        labeled_files = glob.glob(os.path.join(self.adapted_dir, "labeled_leads_*.csv"))
        
        if len(labeled_files) <= keep_latest:
            print(f" Only {len(labeled_files)} files found, no cleanup needed")
            return
        
        # Sort files by modification time (newest first)
        labeled_files.sort(key=os.path.getmtime, reverse=True)
        
        files_to_keep = labeled_files[:keep_latest]
        files_to_delete = labeled_files[keep_latest:]
        
        print(f" Keeping {len(files_to_keep)} latest files")
        print(f" Deleting {len(files_to_delete)} old files:")
        
        for file_path in files_to_delete:
            try:
                filename = os.path.basename(file_path)
                print(f"  - {filename}")
                os.remove(file_path)
            except Exception as e:
                print(f"   Error deleting {filename}: {e}")
        
        print(" Cleanup completed")


def create_master_training_dataset(cleanup_old_files=True):
    """Main function to create master training dataset"""
    
    merger = SmartDataMerger()
    
    # Create master dataset
    master_path, metadata = merger.create_master_dataset()
    
    if master_path is None:
        print(" Failed to create master dataset")
        return None
    
    # Cleanup old files if requested
    if cleanup_old_files:
        merger.cleanup_old_fresh_data(keep_latest=3)
    
    print("\n Master Training Dataset Created Successfully!")
    print(f" Dataset Path: {master_path}")
    
    if metadata:
        stats = metadata["merge_statistics"]
        print(f" CRM Records: {stats['crm_records']}")
        print(f" Fresh Records: {stats['fresh_records']}")
        print(f" Final Records: {stats['final_records']}")
        print(f" Duplicates Removed: {stats['deduplication']['duplicates_removed']}")
    
    return master_path, metadata


if __name__ == "__main__":
    master_dataset_path, merge_metadata = create_master_training_dataset()
    
    if master_dataset_path:
        print(f"\n Ready for model retraining!")
        print(f" Use dataset: {master_dataset_path}")
    else:
        print(f"\n Master dataset creation failed!")
